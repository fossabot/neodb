import uuid
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.translation import gettext_lazy as _
from django.http import (
    HttpResponseBadRequest,
    HttpResponseServerError,
    HttpResponse,
    HttpResponseRedirect,
    HttpResponseNotFound,
)
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import Count
from django.utils import timezone
from django.core.paginator import Paginator
from polymorphic.base import django
from catalog.common.models import SiteName
from catalog.common.sites import AbstractSite, SiteManager
from mastodon import mastodon_request_included
from mastodon.models import MastodonApplication
from mastodon.api import share_mark, share_review
from ..models import *
from django.conf import settings
from django.utils.baseconv import base62
from journal.models import Mark, ShelfMember, Review
from journal.models import query_visible, query_following
from common.utils import PageLinksGenerator
from common.config import PAGE_LINK_NUMBER
from journal.models import ShelfTypeNames
import django_rq
from rq.job import Job
from .external import ExternalSources

_logger = logging.getLogger(__name__)


class HTTPResponseHXRedirect(HttpResponseRedirect):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self["HX-Redirect"] = self["Location"]

    status_code = 200


@login_required
def fetch_refresh(request, job_id):
    retry = request.GET
    job = Job.fetch(id=job_id, connection=django_rq.get_connection("fetch"))
    item_url = job.result if job else "-"  # FIXME job.return_value() in rq 1.12
    if item_url:
        if item_url == "-":
            return render(request, "fetch_failed.html")
        else:
            return HTTPResponseHXRedirect(item_url)
    else:
        retry = int(request.GET.get("retry", 0)) + 1
        if retry > 10:
            return render(request, "fetch_failed.html")
        else:
            return render(
                request,
                "fetch_refresh.html",
                {"job_id": job_id, "retry": retry, "delay": retry * 2},
            )


def fetch(request, url, is_refetch: bool = False, site: AbstractSite = None):
    if not site:
        site = SiteManager.get_site_by_url(url)
        if not site:
            return HttpResponseBadRequest()
    item = site.get_item()
    if item and not is_refetch:
        return redirect(item.url)
    job_id = uuid.uuid4().hex
    django_rq.get_queue("fetch").enqueue(fetch_task, url, is_refetch, job_id=job_id)
    return render(
        request,
        "fetch_pending.html",
        {
            "site": site,
            "job_id": job_id,
        },
    )


def search(request):
    category = request.GET.get("c", default="all").strip().lower()
    if category == "all":
        category = None
    keywords = request.GET.get("q", default="").strip()
    tag = request.GET.get("tag", default="").strip()
    p = request.GET.get("page", default="1")
    page_number = int(p) if p.isdigit() else 1
    if not (keywords or tag):
        return render(
            request,
            "search_results.html",
            {
                "items": None,
            },
        )

    if request.user.is_authenticated and keywords.find("://") > 0:
        site = SiteManager.get_site_by_url(keywords)
        if site:
            return fetch(request, keywords, False, site)
    if settings.SEARCH_BACKEND is None:
        # return limited results if no SEARCH_BACKEND
        result = {
            "items": Items.objects.filter(title__like=f"%{keywords}%")[:10],
            "num_pages": 1,
        }
    else:
        result = Indexer.search(keywords, page=page_number, category=category, tag=tag)
    keys = []
    items = []
    urls = []
    for i in result.items:
        key = (
            i.isbn
            if hasattr(i, "isbn")
            else (i.imdb_code if hasattr(i, "imdb_code") else None)
        )
        if key is None:
            items.append(i)
        elif key not in keys:
            keys.append(key)
            items.append(i)
        for res in i.external_resources.all():
            urls.append(res.url)
    # if request.path.endswith(".json/"):
    #     return JsonResponse(
    #         {
    #             "num_pages": result.num_pages,
    #             "items": list(map(lambda i: i.get_json(), items)),
    #         }
    #     )
    request.session["search_dedupe_urls"] = urls
    return render(
        request,
        "search_results.html",
        {
            "items": items,
            "pagination": PageLinksGenerator(
                PAGE_LINK_NUMBER, page_number, result.num_pages
            ),
            "categories": ["book", "movie", "music", "game"],
            "sites": SiteName.labels,
            "hide_category": category is not None,
        },
    )


@login_required
def external_search(request):
    category = request.GET.get("c", default="all").strip().lower()
    if category == "all":
        category = None
    keywords = request.GET.get("q", default="").strip()
    page_number = int(request.GET.get("page", default=1))
    items = ExternalSources.search(category, keywords, page_number) if keywords else []
    dedupe_urls = request.session.get("search_dedupe_urls", [])
    items = [i for i in items if i.source_url not in dedupe_urls]

    return render(
        request,
        "external_search_results.html",
        {
            "external_items": items,
        },
    )


@login_required
def refetch(request):
    if request.method != "POST":
        return HttpResponseBadRequest()
    url = request.POST.get("url")
    if not url:
        return HttpResponseBadRequest()
    return fetch(request, url, True)


def fetch_task(url, is_refetch):
    item_url = "-"
    try:
        site = SiteManager.get_site_by_url(url)
        site.get_resource_ready(ignore_existing_content=is_refetch)
        item = site.get_item()
        if item:
            _logger.info(f"fetched {url} {item.url} {item}")
            item_url = item.url
        else:
            _logger.error(f"fetch {url} failed")
    except Exception as e:
        _logger.error(f"fetch {url} error {e}")
    return item_url
