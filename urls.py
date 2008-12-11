# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from ragendja.urlsauto import urlpatterns
from myapp.forms import UserRegistrationForm

urlpatterns = patterns('',
    (r'^$', 'django.views.generic.simple.direct_to_template',
        {'template': 'main.html'}),
    # Override the default registration form
    url(r'^account/register/$', 'registration.views.register',
        kwargs={'form_class': UserRegistrationForm},
        name='registration_register'),
) + urlpatterns
