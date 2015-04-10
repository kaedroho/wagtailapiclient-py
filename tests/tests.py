from django.test import LiveServerTestCase

from wagtailapiclient import client


class TestAPIClient(LiveServerTestCase):
    fixtures = ['demosite.json']

    def get_connection(self):
        return client.Connection(self.live_server_url + '/api/v1/')

    def test_get(self):
        page = self.get_connection().pages.get(id=2)

        self.assertIsInstance(page, client.Page)
        self.assertEqual(page.id, 2)
