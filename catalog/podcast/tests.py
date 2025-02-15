from django.test import TestCase
from catalog.podcast.models import *
from catalog.common import *


class ApplePodcastTestCase(TestCase):
    def setUp(self):
        pass

    def test_parse(self):
        t_id = "657765158"
        t_url = "https://podcasts.apple.com/us/podcast/%E5%A4%A7%E5%86%85%E5%AF%86%E8%B0%88/id657765158"
        t_url2 = "https://podcasts.apple.com/us/podcast/id657765158"
        p1 = SiteManager.get_site_by_id_type(IdType.ApplePodcast)
        self.assertIsNotNone(p1)
        self.assertEqual(p1.validate_url(t_url), True)
        p2 = SiteManager.get_site_by_url(t_url)
        self.assertEqual(p1.id_to_url(t_id), t_url2)
        self.assertEqual(p2.url_to_id(t_url), t_id)

    @use_local_response
    def test_scrape(self):
        t_url = "https://podcasts.apple.com/gb/podcast/the-new-yorker-radio-hour/id1050430296"
        site = SiteManager.get_site_by_url(t_url)
        self.assertEqual(site.ready, False)
        self.assertEqual(site.id_value, "1050430296")
        site.get_resource_ready()
        self.assertEqual(site.resource.metadata["title"], "The New Yorker Radio Hour")
        # self.assertEqual(site.resource.metadata['feed_url'], 'http://feeds.wnyc.org/newyorkerradiohour')
        self.assertEqual(
            site.resource.metadata["feed_url"],
            "http://feeds.feedburner.com/newyorkerradiohour",
        )
