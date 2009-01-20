# -*- coding: utf-8 -*-
"""
Provides basic set of auth urls.
"""
from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('')

LOGIN = '^%s$' % settings.LOGIN_URL.lstrip('/')
LOGOUT = '^%s$' % settings.LOGOUT_URL.lstrip('/')

# register auth urls depending on whether we use google or hybrid auth
if 'ragendja.auth.middleware.GoogleAuthenticationMiddleware' in \
        settings.MIDDLEWARE_CLASSES:
    urlpatterns += patterns('',
        url(LOGIN, 'ragendja.auth.views.google_login',
            name='django.contrib.auth.views.login'),
        url(LOGOUT, 'ragendja.auth.views.google_logout', {'next_page': '/'},
            name='django.contrib.auth.views.logout'),
    )
elif 'ragendja.auth.middleware.HybridAuthenticationMiddleware' in \
        settings.MIDDLEWARE_CLASSES:
    urlpatterns += patterns('',
        url(LOGIN, 'ragendja.auth.views.hybrid_login',
            name='django.contrib.auth.views.login'),
        url(LOGOUT, 'ragendja.auth.views.hybrid_logout', {'next_page': '/'},
            name='django.contrib.auth.views.logout'),
    )
else:
    urlpatterns += patterns('',
        url(LOGIN, 'django.contrib.auth.views.login'),
        url(LOGOUT, 'django.contrib.auth.views.logout', {'next_page': '/'}),
    )
