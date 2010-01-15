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
import prowlpy
import datetime
import logging
from libcloud.types import Provider
from libcloud.providers import get_driver
from google.appengine.api import urlfetch

class Dashboard(webapp.RequestHandler):
	def __init__(self):	
		self.utilization_rate = .9
		self.instances2var = {'us-east-1.linux.m1.small'	: 'us_east_small_linux_data', 
			'us-west-1.linux.m1.small'	: 'us_west_small_linux_data', 
			'eu-west-1.linux.m1.small'	: 'eu_west_small_linux_data'}

		self.instances_privcost = {'us-east-1.linux.m1.small'	: str(350/(self.utilization_rate*365*24)+0.03),
			'us-west-1.linux.m1.small'	: str(350/(self.utilization_rate*365*24)+0.04),
			'eu-west-1.linux.m1.small'	: str(350/(self.utilization_rate*365*24)+0.04)}

		self.instances_basiccost = {'us-east-1.linux.m1.small'	: '0.085',
			'us-west-1.linux.m1.small'	: '0.095',
			'eu-west-1.linux.m1.small'	: '0.095'}

	def get(self):
		adminoptions    = AdminOptions.get_by_key_name('credentials')
		if adminoptions:
			monitoroptions  = EC2PricingMonitor.get_by_key_name(adminoptions.accountname)
			if monitoroptions:
				serverlist = db.GqlQuery("SELECT * FROM Server")
				user = users.get_current_user()
				input_data_settings = {}
				for instance in self.instances2var.keys():
					url = "http://www.cloudexchange.org/data/"+instance+".csv"
					logging.info("fetching from URL: %s" % url)
					try:
						result = urlfetch.fetch(url)
						logging.info("return code : %s" % result.status_code)
					except:
						logging.info("got exception from urlfetch")
					if result.status_code == 200:
						content = result.content
						logging.info("content : %s" % content)
						input_data_settings[instance] = r"<settings><data_sets><data_set did='0'><csv><data>%s</data></csv></data_set></data_sets></settings>" % content.replace('\n',','+self.instances_privcost[instance]+','+self.instances_basiccost[instance]+'\\n')
						logging.info("input_data_settings: %s" % input_data_settings[instance])
					else:
						input_data_settings[instance] = r"<settings><data_sets><data_set did='0'><csv><data>2009-11-30 21:21:21,0.029\n2009-12-01 05:12:36,0.029\n2009-12-01 05:12:37,0.03\n2009-12-01 09:59:04,0.03</data></csv></data_set></data_sets></settings>"
						logging.info("input_data_settings: %s" % input_data_settings[instance])
				template_values = {}
				for instance,variable in self.instances2var.iteritems():
					template_values[variable] = input_data_settings[instance]
				template_values['monitoroptions'] = monitoroptions
#				template_values = {'eu_west_small_linux_data': input_data_settings['eu-west-1.linux.m1.small'],'us_west_small_linux_data': input_data_settings['us-west-1.linux.m1.small'],'us_east_small_linux_data': input_data_settings['us-east-1.linux.m1.small'],}
				path = os.path.join(os.path.dirname(__file__), 'dashboard.html')
				self.response.out.write(template.render(path, template_values))
			else :
				self.redirect('/admin')
		else :
			self.redirect('/admin')
        
        
def main():
	application = webapp.WSGIApplication([('/dashboard', Dashboard)],debug=True)
	wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
	main()
