from django.conf import settings
from django.contrib.sites.models import Site
from django.utils._threading_local import local

_default_site_id = getattr(settings, 'SITE_ID', None)
_site_id = local()

class SiteID(object):
    def __get__(self, settings, cls):
        if not _site_id.value:
            raise ValueError('SITE_ID not defined in settings')
        return _site_id.value

settings.__class__.SITE_ID = SiteID()

class DynamicSiteIDMiddleware(object):
    """Sets settings.SIDE_ID based on request's domain"""
    def process_request(self, request):
        # Ignore port
        host = request.get_host().split(':')[0]

        # Try exact domain and fall back to with/without 'www.'
        site = Site.all().filter('domain =', host).get()
        if not site:
            if host.startswith('www.'):
                host = host[4:]
            else:
                host = 'www.' + host
            site = Site.all().filter('domain =', host).get()

        if site:
            _site_id.value = str(site.key())
        else:
            _site_id.value = _default_site_id
