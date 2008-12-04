# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from myapp.forms import UserRegistrationForm

urlpatterns = patterns('',
    (r'^$', 'django.views.generic.simple.direct_to_template',
        {'template': 'main.html'}),
    (r'^person/', include('myapp.urls')),
    url(r'^accounts/register/$', 'registration.views.register',
        kwargs={'form_class': UserRegistrationForm},
        name='registration_register'),
    (r'^accounts/', include('registration.urls')),
)
