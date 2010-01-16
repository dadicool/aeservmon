#!/usr/bin/env python
# Copyright (c) 2009, Steve Oliver (steve@xercestech.com)
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without
#modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the <organization> nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
#THIS SOFTWARE IS PROVIDED BY STEVE OLIVER ''AS IS'' AND ANY
#EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#DISCLAIMED. IN NO EVENT SHALL STEVE OLIVER BE LIABLE FOR ANY
#DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.



import httplib
import cgi
import wsgiref.handlers
from models import Server, AdminOptions, EC2Account, EC2PricingMonitor
import os
from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.db import Key
import time
import sys
import prowlpy
import datetime
import logging
from libcloud.types import Provider
from libcloud.providers import get_driver


class Admin(webapp.RequestHandler):
	def get(self):
		adminoptions = AdminOptions.get_by_key_name('credentials')
		if adminoptions:  
			twitterpass = adminoptions.twitterpass
			twitteruser = adminoptions.twitteruser
			prowlkey = adminoptions.prowlkey
			monitoroptions = EC2PricingMonitor.get_by_key_name(adminoptions.accountname)
			logging.info("accountname = %s" % adminoptions.accountname)
		else:
			twitterpass = "Change Me"
			twitteruser = "Change Me"
			prowlkey = "Change Me"
			monitoroptions = EC2PricingMonitor();
		serverlist = db.GqlQuery("SELECT * FROM Server")
		user = users.get_current_user()
		template_values = {'user': user, 'twitteruser': twitteruser, 'twitterpass': twitterpass, 'serverlist': serverlist, 'prowlkey': prowlkey, 'adminoptions': adminoptions,'monitoroptions': monitoroptions}
		path = os.path.join(os.path.dirname(__file__), 'admin.html')
		self.response.out.write(template.render(path, template_values))
        
class StoreServer(webapp.RequestHandler):
	def post(self):	
		server = Server(key_name=self.request.get('serverdomain'))
		server.serverdomain = self.request.get('serverdomain')
		if self.request.get('ssl') == "True":
			server.ssl = True
		else:
			server.ssl = False
		if self.request.get('serverport') != None:
			server.serverport = self.request.get('serverport')
		else:
			if server.ssl:
				server.serverport = str(':443')
			else:          
				server.serverport = str(':80"')
		if self.request.get('notifywithprowl') == "True":
			server.notifywithprowl = True
		if self.request.get('notifywithemail') == "True":
			server.notifywithemail = True
		#server.notifywithprowl = self.request.get('notifywithtwitter')
		server.email = users.get_current_user().email()
		server.put()
		self.redirect('/admin')

class StoreEC2Account(webapp.RequestHandler):
	def post(self):	
		adminoptions = AdminOptions(key_name="credentials")
		logging.info('Post for Account %s' % self.request.get('accountname'))
		if self.request.get('accountname'):
			account = EC2Account(key_name=self.request.get('accountname'))
			adminoptions.accountname = self.request.get('accountname')
			account.ec2apikey = self.request.get('ec2apikey')
			account.ec2secretkey = self.request.get('ec2secretkey')
#			EC2 = get_driver(Provider.EC2)
#			driver = [ EC2(account.ec2apikey,account.ec2secretkey) ]
#			try:
#				nodes = driver.list_nodes()
#			except:
#				logging.info('Invalid EC2 credentials for Account : %s with exception: %s' % (self.request.get('accountname'),sys.exc_type))
#				self.redirect('/admin')
#				return
			account.put()
			adminoptions.put()
		
		self.redirect('/admin')
        
class StoreEC2Monitor(webapp.RequestHandler):
	def post(self):	
		adminoptions = AdminOptions.get_by_key_name("credentials")
		logging.info('Post for Account %s' % adminoptions.accountname)
		account = EC2PricingMonitor(key_name=adminoptions.accountname)
		account.privateinstanceutilization = int(self.request.get('utilization'))
		logging.info("checkbox output %s" % self.request.get('us_east_small_linux_valid'))
		if self.request.get('us_east_small_linux_valid') == "on":
			account.us_east_small_linux_valid = True
		else:
			account.us_east_small_linux_valid = False

		if self.request.get('us_west_small_linux_valid') == "on":
			account.us_west_small_linux_valid = True
		else:
			account.us_west_small_linux_valid = False

		if self.request.get('eu_west_small_linux_valid') == "on":
			account.eu_west_small_linux_valid = True
		else:
			account.eu_west_small_linux_valid = False
		if self.request.get('us_east_large_linux_valid') == "on":
			account.us_east_large_linux_valid = True
		else:
			account.us_east_large_linux_valid = False

		if self.request.get('us_west_large_linux_valid') == "on":
			account.us_west_large_linux_valid = True
		else:
			account.us_west_large_linux_valid = False

		if self.request.get('eu_west_large_linux_valid') == "on":
			account.eu_west_large_linux_valid = True
		else:
			account.eu_west_large_linux_valid = False
		account.put()
		self.redirect('/admin')
        
class DeleteServer(webapp.RequestHandler):
	def post(self):
		serverdomain = self.request.get('serverdomain')
		server = Server.get_by_key_name(serverdomain)
		server.delete()
		self.redirect('/admin')
        
class StoreAdminOptions(webapp.RequestHandler):
	def post(self):        
		adminoptions = AdminOptions(key_name="credentials")
		adminoptions.twitteruser = self.request.get('twitteruser')
		adminoptions.twitterpass = self.request.get('twitterpass')
		adminoptions.prowlkey = self.request.get('prowlkey')
		prowlnotifier = prowlpy.Prowl(self.request.get('prowlkey'))
		try:
			adminoptions.prowlkeyisvalid = prowlnotifier.verify_key()
		except:
			adminoptions.prowlkeyisvalid = False
		adminoptions.put()
		self.redirect('/admin')
        
        
def main():
	application = webapp.WSGIApplication([('/admin/storeserver', StoreServer),('/admin/storeec2monitor', StoreEC2Monitor),('/admin/storeec2account', StoreEC2Account),('/admin/deleteserver', DeleteServer),('/admin/storeadminoptions', StoreAdminOptions),('/admin', Admin)],debug=True)
	wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
	main()
