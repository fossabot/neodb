from django.test import TestCase
from catalog.common import *
from catalog.models import *


class SpotifyTestCase(TestCase):
    def test_parse(self):
        t_id_type = IdType.Spotify_Album
        t_id_value = "65KwtzkJXw7oT819NFWmEP"
        t_url = "https://open.spotify.com/album/65KwtzkJXw7oT819NFWmEP"
        site = SiteManager.get_site_by_id_type(t_id_type)
        self.assertIsNotNone(site)
        self.assertEqual(site.validate_url(t_url), True)
        site = SiteManager.get_site_by_url(t_url)
        self.assertEqual(site.url, t_url)
        self.assertEqual(site.id_value, t_id_value)

    @use_local_response
    def test_scrape(self):
        t_url = "https://open.spotify.com/album/65KwtzkJXw7oT819NFWmEP"
        site = SiteManager.get_site_by_url(t_url)
        self.assertEqual(site.ready, False)
        site.get_resource_ready()
        self.assertEqual(site.ready, True)
        self.assertEqual(site.resource.metadata["title"], "The Race For Space")
        self.assertIsInstance(site.resource.item, Album)
        self.assertEqual(site.resource.item.barcode, "3610159662676")


class DoubanMusicTestCase(TestCase):
    def test_parse(self):
        t_id_type = IdType.DoubanMusic
        t_id_value = "33551231"
        t_url = "https://music.douban.com/subject/33551231/"
        site = SiteManager.get_site_by_id_type(t_id_type)
        self.assertIsNotNone(site)
        self.assertEqual(site.validate_url(t_url), True)
        site = SiteManager.get_site_by_url(t_url)
        self.assertEqual(site.url, t_url)
        self.assertEqual(site.id_value, t_id_value)

    @use_local_response
    def test_scrape(self):
        t_url = "https://music.douban.com/subject/33551231/"
        site = SiteManager.get_site_by_url(t_url)
        self.assertEqual(site.ready, False)
        site.get_resource_ready()
        self.assertEqual(site.ready, True)
        self.assertEqual(site.resource.metadata["title"], "The Race For Space")
        self.assertIsInstance(site.resource.item, Album)
        self.assertEqual(site.resource.item.barcode, "3610159662676")


class MultiMusicSitesTestCase(TestCase):
    @use_local_response
    def test_albums(self):
        url1 = "https://music.douban.com/subject/33551231/"
        url2 = "https://open.spotify.com/album/65KwtzkJXw7oT819NFWmEP"
        p1 = SiteManager.get_site_by_url(url1).get_resource_ready()
        p2 = SiteManager.get_site_by_url(url2).get_resource_ready()
        self.assertEqual(p1.item.id, p2.item.id)


class BandcampTestCase(TestCase):
    def test_parse(self):
        t_id_type = IdType.Bandcamp
        t_id_value = "intlanthem.bandcamp.com/album/in-these-times"
        t_url = "https://intlanthem.bandcamp.com/album/in-these-times?from=hpbcw"
        t_url2 = "https://intlanthem.bandcamp.com/album/in-these-times"
        site = SiteManager.get_site_by_id_type(t_id_type)
        self.assertIsNotNone(site)
        self.assertEqual(site.validate_url(t_url), True)
        site = SiteManager.get_site_by_url(t_url)
        self.assertEqual(site.url, t_url2)
        self.assertEqual(site.id_value, t_id_value)

    @use_local_response
    def test_scrape(self):
        t_url = "https://intlanthem.bandcamp.com/album/in-these-times?from=hpbcw"
        site = SiteManager.get_site_by_url(t_url)
        self.assertEqual(site.ready, False)
        site.get_resource_ready()
        self.assertEqual(site.ready, True)
        self.assertEqual(site.resource.metadata["title"], "In These Times")
        self.assertEqual(site.resource.metadata["artist"], ["Makaya McCraven"])
        self.assertIsInstance(site.resource.item, Album)
