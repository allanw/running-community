from django.conf.urls.defaults import *

urlpatterns = patterns('runs.views',
    #(r'^$', 'django.views.generic.simple.direct_to_template', {'template': 'index.html'}),
    (r'^$', 'index'),
    url(r'^nikeplus/$', 'get_nike_plus_data', name="get_nike_plus_data"),
    (r'my_test/$', 'my_test'),
    (r'^create/$', 'add_poll'),
    (r'^(?P<key>.+)/$', 'detail'),
    (r'^(?P<poll_id>\d+)/results/$', 'results'),
    (r'^(?P<poll_id>\d+)/vote/$', 'vote'),
)
