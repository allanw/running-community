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
        domain = request.get_host().split(':')[0]

        # Try exact domain and fall back to with/without 'www.'
        site = Site.all().filter('domain =', domain).get()
        if not site:
            if domain.startswith('www.'):
                fallback_domain = domain[4:]
            else:
                fallback_domain = 'www.' + domain
            site = Site.all().filter('domain =', fallback_domain).get()

        # Add site if it doesn't exist
        if not site and getattr(settings, 'CREATE_SITES_AUTOMATICALLY', True):
            site = Site(domain=domain, name=domain)
            site.put()

        # Set SITE_ID for this thread/request
        if site:
            _site_id.value = str(site.key())
        else:
            _site_id.value = _default_site_id
