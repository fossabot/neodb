import logging
from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponseBadRequest, HttpResponseServerError, HttpResponse
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import Count
from django.utils import timezone
from django.core.paginator import Paginator
from mastodon import mastodon_request_included
from mastodon.models import MastodonApplication
from mastodon.api import share_mark, share_review
from .models import *
from django.conf import settings
from common.scraper import get_scraper_by_url, get_normalized_url
from django.utils.baseconv import base62
from journal.models import Mark, ShelfMember, Review
from journal.models import query_visible, query_following
from common.utils import PageLinksGenerator
from common.views import PAGE_LINK_NUMBER
from journal.models import ShelfTypeNames

_logger = logging.getLogger(__name__)


NUM_REVIEWS_ON_ITEM_PAGE = 5
NUM_REVIEWS_ON_LIST_PAGE = 20


def retrieve_by_uuid(request, item_uid):
    item = get_object_or_404(Item, uid=item_uid)
    return redirect(item.url)


def retrieve(request, item_path, item_uuid):
    if request.method == 'GET':
        item = get_object_or_404(Item, uid=base62.decode(item_uuid))
        item_url = f'/{item_path}/{item_uuid}'
        if item.url != item_url:
            return redirect(item.url)
        mark = None
        review = None
        mark_list = None
        review_list = None
        collection_list = []
        shelf_types = [(n[1], n[2]) for n in iter(ShelfTypeNames) if n[0] == item.category]
        if request.user.is_authenticated:
            visible = query_visible(request.user)
            mark = Mark(request.user, item)
            _logger.info(mark.rating)
            review = mark.review
            collection_list = item.collections.all().filter(visible).annotate(like_counts=Count('likes')).order_by('-like_counts')
            mark_query = ShelfMember.objects.filter(item=item).filter(visible).order_by('-created_time')
            mark_list = [member.mark for member in mark_query[:NUM_REVIEWS_ON_ITEM_PAGE]]
            review_list = Review.objects.filter(item=item).filter(visible).order_by('-created_time')[:NUM_REVIEWS_ON_ITEM_PAGE]

        return render(request, item.class_name + '.html', {
            'item': item,
            'mark': mark,
            'review': review,
            'mark_list': mark_list,
            'review_list': review_list,
            'collection_list': collection_list,
            'shelf_types': shelf_types,
        }
        )
    else:
        return HttpResponseBadRequest()


def mark_list(request, item_path, item_uuid, following_only=False):
    item = get_object_or_404(Item, uid=base62.decode(item_uuid))
    if not item:
        return HttpResponseNotFound("item not found")
    queryset = ShelfMember.objects.filter(item=item).order_by('-created_time')
    if following_only:
        queryset = queryset.filter(query_following(request.user))
    else:
        queryset = queryset.filter(query_visible(request.user))
    paginator = Paginator(queryset, NUM_REVIEWS_ON_LIST_PAGE)
    page_number = request.GET.get('page', default=1)
    marks = paginator.get_page(page_number)
    marks.pagination = PageLinksGenerator(
        PAGE_LINK_NUMBER, page_number, paginator.num_pages)
    return render(
        request,
        'item_mark_list.html',
        {
            'marks': marks,
            'item': item,
        }
    )


def review_list(request, item_path, item_uuid):
    item = get_object_or_404(Item, uid=base62.decode(item_uuid))
    if not item:
        return HttpResponseNotFound("item not found")
    queryset = Review.objects.filter(item=item).order_by('-created_time')
    queryset = queryset.filter(query_visible(request.user))
    paginator = Paginator(queryset, NUM_REVIEWS_ON_LIST_PAGE)
    page_number = request.GET.get('page', default=1)
    reviews = paginator.get_page(page_number)
    reviews.pagination = PageLinksGenerator(
        PAGE_LINK_NUMBER, page_number, paginator.num_pages)
    return render(
        request,
        'item_review_list.html',
        {
            'reviews': reviews,
            'item': item,
        }
    )
