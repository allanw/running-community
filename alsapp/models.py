# -*- coding: utf-8 -*-
from django.db.models import permalink
from django.contrib.auth.models import User
from google.appengine.ext import db
import datetime

class Poll(db.Model):
	question = db.StringProperty()
	pub_date = db.DateTimeProperty('date published')
	
	def was_published_today(self):
		return self.pub_date.date() == datetime.date.today()
	was_published_today.short_description = 'Published today?'
	
	def __unicode__(self):
		return self.question

	@permalink
	def get_absolute_url(self):
		return ('alsapp.views.detail', (), {'key': self.key()})
	
class Choice(db.Model):
	poll = db.ReferenceProperty(Poll)
	choice = db.StringProperty()
	votes = db.IntegerProperty()
	
	def __unicode__(self):
		return self.choice
		
class NikePlusInfo(db.Model):
	user_id = db.StringProperty()
	
	def __unicode__(self):
		return self.user_id + ' : ' + str(self.last_scrape)
		
class Run(db.Model):
	run_id = db.StringProperty()
	user = db.ReferenceProperty(User,
                                   collection_name='runs')
	run_time = db.DateTimeProperty('start time of run')
	distance = db.FloatProperty()
	#duration = db.IntegerProperty()
	#calories = db.FloatProperty()
	#description = db.StringProperty()