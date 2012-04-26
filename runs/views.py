# -*- coding: utf-8 -*-
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from ragendja.template import render_to_response
from runs.models import Poll, NikePlusInfo, Run
from runs.forms import PollForm
from django.views.generic.list_detail import object_list, object_detail
from django.views.generic.create_update import create_object
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import urlfetch
import urllib2
import datetime
from xml.dom import minidom
import math
import Cookie

def index(request):
		#user = User.get_by_key_name("key_"+self.cleaned_data['username'].lower())
		username = request.user.username
		user = User.get_by_key_name("key_"+username.lower())
		if user and user.is_active:
			last_scrape = user.nike_last_scrape
		else:
			last_scrape = None
		return object_list(request, Run.all().filter('user =', user).order('-run_time'),
		                   extra_context={'last_scrape':last_scrape})
	
def detail(request, key):
	# isn't there a better way to do this?
	# e.g. by doing p = Poll.get_by_key_name(key) - didn't seem to work for me
	p = db.get(key)
	return object_detail(request, Run.all(), key)
	
def results(request):
	return HttpResponse("hi")

def vote(request):
	return HttpResponse("hello")
	
def add_poll(request):
	return create_object(request, form_class=PollForm,
        post_save_redirect=reverse('runs.views.detail',
                                   kwargs=dict(key='%(key)s')))


# TODO: have a separate view to view all Nike+ runs and choose which ones to import
# tell the user how many new runs they have
# the get_nike_plus_data function can be used to just pull down new runs

# TODO: upon registration, they enter their Nike ID and then an initial scrape is performed?


def get_nike_plus_data(request):


	# TODO: protect against the case where a user_id hasn't been set. force this to be set upon registration?
	# TODO: Only set new last_scrape_time if the scrape is successful
	
	username = request.user.username
	user = User.get_by_key_name("key_"+username.lower())
	
	if user and user.is_active:
		last_scrape_time = user.nike_last_scrape
		userId = user.nike_user_id
	else:
		last_scrape_time = None
		
	if not last_scrape_time:
		last_scrape_time = datetime.datetime(1970, 1, 1) # Set it to an arbitrary early date
				
	#response = urllib2.urlopen('http://nikeplus.nike.com/nikeplus/v1/services/widget/get_public_run_list.jsp?userID=%s' % userId).read()
	#response = urlfetch.fetch('https://secure-nikerunning.nike.com/nikeplus/v1/services/app/run_list.jsp')
	#response = urlfetch.fetch('http://nikerunning.nike.com/nikeplus/v2/services/app/run_list.jsp?userID=%s&startIndex=0&endIndex=5' % userId)
	
	# don't specify startIndex and endIndex in the URL i.e. get all runs
	response = urlfetch.fetch('http://nikerunning.nike.com/nikeplus/v2/services/app/run_list.jsp?userID=%s' % userId)
	import logging
	logging.debug(response.content)		
	
	dom = minidom.parseString(response.content)
	
	run_ids_and_times = []
	# N.B. in the following code I replaced 'startTime' with 'syncTime' - this makes sense
	
	# AUG 14TH 2010 - NOTE - THIS IS PROBABLY REALLY INEFFICIENT!!!
	# WOULD BE BETTER TO LIMIT THE AMOUNT OF RUNS I GET IN THE REQUEST (i.e. use startIndex/endIndex)
	# THIS LIMIT NEEDS TO BE BASED ON nike_last_scrape
	#
	# IDEA: START AT END OF XML FILE AND MOVE BACKWARDS, CHECKING THE syncTime value until
	# it becomes earlier than nike_last_scrape 
	for run in dom.getElementsByTagName('run'):
		run_id = run.getAttribute('id')
		
		sync_time = run.getElementsByTagName('syncTime')[0]
		sync_time = sync_time.toxml()
		sync_time = sync_time.replace('<syncTime>', '') # Get rid of the opening syncTime tag
		sync_time = sync_time.split('+')[0] # Strip off the time zone stuff and closing tag
		sync_time = datetime.datetime.strptime(sync_time, '%Y-%m-%dT%H:%M:%S')
		
		run_ids_and_times.append((run_id, sync_time))
		##run = Run(run_id=run_id, run_time=run_time)
		##run.put()
		
	# Only keep the runs which have been synced after the last_scrape_time
	run_ids_and_times = [(run_id, t) for (run_id, t) in run_ids_and_times if t > last_scrape_time]

	# Set last scrape time to now
	# TODO - uncomment the following line
	#user.nike_last_scrape = datetime.datetime.now()
	user.put()
	
	# No new runs so just return
	# TODO: Give the user some feedback e.g. a message saying 'No new runs'
	if len(run_ids_and_times) == 0:
		return HttpResponseRedirect('/runs/')
		
	cookie = Cookie.SimpleCookie()
	cookie.load(response.headers.get('set-cookie', ''))
	cookie['plusid'] = user.nike_user_id +"&nikerunning.nike.com"
	headers = {
				'Host' : 'runlogger.appspot.com',
				'User-Agent' : 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2 (.NET CLR 3.5.30729)',
				'Cookie' : _makeCookieHeader(cookie)
			  }
	
	# Save the new run(s)
	for run in dom.getElementsByTagName('run'):
		for (run_id, t) in run_ids_and_times:
			if run.getAttribute('id') == run_id:
				
				# Get the time the run started
				run_time = run.getElementsByTagName('startTime')[0]
				run_time = run_time.toxml()
				run_time = run_time.replace('<startTime>', '') # Get rid of the opening startTime tag
				run_time = run_time.split('+')[0] # Strip off the time zone stuff and closing tag
				run_time = datetime.datetime.strptime(run_time, '%Y-%m-%dT%H:%M:%S')
				
				distance = run.getElementsByTagName('distance')[0]
				distance = distance.toxml()
				distance = distance.replace('<distance>', '')
				distance = distance.replace('</distance>', '')
				
				dist_len = len('%.2f' % float(distance)) # Length of distance string when truncated to 2 D.P.
				distance = float(distance[:dist_len])
				
				duration = run.getElementsByTagName('duration')[0]
				duration = duration.toxml()
				duration = duration.replace('<duration>', '')
				duration = duration.replace('</duration>', '')
				# TODO - TEST OUT THIS CODE WITH RUNS OVER AN HOUR LONG - WILL IT WORK?
				duration = float(duration)/1000/60 # Convert duration in ms to minutes
				decimal_part_of_mins, mins = math.modf(duration)
				gt_1hour = False
				if mins >= 60:
					gt_1hour = True
					mins_when_duration_gt_1hour, hours = math.modf(mins/60)
					mins = mins_when_duration_gt_1hour * 60
					
				secs = decimal_part_of_mins * 60
				
				if gt_1hour:
					duration_pretty = '%s:%s:%02d' % (int(hours), int(round(mins)), int(round(secs)))
				else:
					duration_pretty = '%s:%02d' % (int(mins), int(round(secs)))
				
				# Get GPX data
				# TODO - don't hardcode the run ID!
				response = urlfetch.fetch('https://secure-nikerunning.nike.com/nikeplus/v2/services/app/get_gps_detail.jsp?_plus=true&id=%s&format=json' % run_id, headers=headers)
				
				logging.debug('gpx data is:')
				logging.debug(response.content)			
				new_run = Run(user=user, run_id=run_id, run_time=run_time, distance=distance, 
								duration=duration, duration_pretty=duration_pretty, gpx_data=unicode(response.content))
				new_run.put()
	
	return HttpResponseRedirect('/runs/')

def _makeCookieHeader(cookie):
    cookieHeader = ""
    for value in cookie.values():
        cookieHeader += "%s=%s; " % (value.key, value.value)
    return cookieHeader

def my_test(request):

    nike_id = request.GET.get('nike_id', None)
    nike_password = request.GET.get('nike_password', None)
	
    callback = request.GET.get('callback', None)

	
	#import cookielib

	#cj = cookielib.LWPCookieJar()

	#opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
	#urllib2.install_opener(opener)

	#theurl2 = 'https://secure-nikeplus.nike.com/nikeplus/v1/services/app/get_user_data.jsp'
	
	#theurl3 = 'https://secure-nikeplus.nike.com/nikeplus/v1/services/app/generate_pin.jhtml?action=login&login=myemail&password=mypassword&locale=en_us'
	
	#foo = urllib2.urlopen(theurl3).read()
	#dom = minidom.parseString(foo)
	#pin = dom.getElementsByTagName('pin')[0].toxml()
	#pin = pin.replace('<pin>', '')
	#pin = pin.replace('</pin>', '')

	#req = urllib2.Request('https://www.nike.com/nikeplus' + '?token=%s' % pin)

	#handle = urllib2.urlopen(req).read()
	
	#req2 = urllib2.Request(theurl2 + '?token=%s' % pin)
	#handle2 = urllib2.urlopen(req2).read()
	
	#req2 = urllib2.Request(theurl2, data=handle)
	
	#handle2 = urllib2.urlopen(req2).read()
	
	#return HttpResponse('hello', mimetype='application/json')

    import urllib2
    import cookielib
    cj = cookielib.LWPCookieJar()

    #theurl = 'https://secure-nikeplus.nike.com/services/profileService?action=login&login=%s&password=%s&locale=en_us' % (nike_id, nike_password)
    theurl = 'https://secure-nikeplus.nike.com/nsl/services/user/login?app=b31990e7-8583-4251-808f-9dc67b40f5d2&format=json&contentType=plaintext'

    import Cookie
    cookie = Cookie.SimpleCookie()
    headers = {
               'Host' : 'runlogger.appspot.com',
               'User-Agent' : 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2 (.NET CLR 3.5.30729)',
               'Cookie' : _makeCookieHeader(cookie),
               'Content-Type': 'application/x-www-form-urlencoded'
               }

    form_fields = {
        "email": nike_id,
        "password": nike_password,
    }
    import urllib
    form_data = urllib.urlencode(form_fields)

    response = urlfetch.fetch(url=theurl, payload=form_data, method=urlfetch.POST, headers=headers, deadline=10)
    import logging
    logging.debug('response is::: %s' % response.content)

    cookie.load(response.headers.get('set-cookie', ''))

    # N.B. REDEFINE THE COOKIE HERE, AFTER LOADING THE COOKIE AS ABOVE
    # TODO: REFACTOR THIS. THERE WILL BE A NEATER WAY
    headers = {
               'Host' : 'runlogger.appspot.com',
               'User-Agent' : 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2 (.NET CLR 3.5.30729)',
               'Cookie' : _makeCookieHeader(cookie)
               }

    #return HttpResponse(response.headers)

    #opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    #urllib2.install_opener(opener)


    theurl2 = 'https://secure-nikeplus.nike.com/nikeplus/v1/services/app/get_user_data.jsp'


    #req = urllib2.Request(theurl)
    #handle = urllib2.urlopen(req).read()

    #req2 = urllib2.Request(theurl2)
    #handle2 = urllib2.urlopen(req2).read()

    response = urlfetch.fetch(url=theurl2,headers=headers)

    from xml.dom import minidom
    logging.debug(response.content)
    dom = minidom.parseString(response.content)
    id = dom.getElementsByTagName('user')[0].getAttribute('id')

    return HttpResponse(id, mimetype='application/json')

    #return HttpResponse(handle2)

    #from xml.dom import minidom
    #dom = minidom.parseString(handle2)
    #foo = dom.getElementsByTagName('user')[0].getAttribute('id')

    #return HttpResponse(foo, mimetype='application/json')
    #return HttpResponse(callback + 'hello')
