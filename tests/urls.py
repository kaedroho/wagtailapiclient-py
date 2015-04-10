from django.conf.urls import url, include

from wagtail.contrib.wagtailapi import urls as wagtailapi_urls


urlpatterns = [
    url(r'^api/', include(wagtailapi_urls)),
]
