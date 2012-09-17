#-*- coding: UTF-8 -*-
import urllib,urllib2,httplib,cookielib
import re,json
import Cookie
import time
import string
from datetime import datetime


def get_cookie(id,password):
	info={}
	postdata=urllib.urlencode({'login_username':id,'login_loginpass':password})
	b=urlfetch.fetch(url="http://wappass.baidu.com/passport/",payload=postdata,method=urlfetch.POST)
	cookie=Cookie.SimpleCookie(b.headers.get('set-cookie'))
	try:
		bduss='BDUSS='+cookie['BDUSS'].value
		info['id']=id
		info['password']=password
		info['cookie']=bduss
		return info
	except:
		return info
		
def checkin(user):
	#get_tbs
	cookies=cookielib.CookieJar()
	opener=urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies))
	urllib2.install_opener(opener)
	headers={'Cookie':user.cookie}
	tbs_url="http://tieba.baidu.com/dc/common/tbs"
	tbs_request = urllib2.Request(tbs_url,None,headers)
	tbs_response=opener.open(tbs_request).read()
	tbs_tbs=re.compile('"(.*?)"').findall(tbs_response)[1]
	#Checkin
	url_checkin="http://tieba.baidu.com/sign/add"
	body='ie=utf-8&kw=firefox&tbs='+tbs_tbs
	re_checkin=urllib2.Request(url_checkin,body,headers)
	retval=urllib2.urlopen(re_checkin).read()
	dict=json.loads(retval)
	if dict['no']==0 or dict['no']==1101:
		return 1
	if dict['no']==4:
		return 2
	else:
		return 0
	
import webapp2
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import urlfetch
from google.appengine.ext import db

class user(db.Model):
	uid = db.StringProperty()
	cookie = db.StringProperty()
	password = db.StringProperty()
	isok=db.IntegerProperty()
	last = db.DateTimeProperty()
	err = db.IntegerProperty()	

class MainHandler(webapp2.RequestHandler):
	def post(self):
		id=self.request.get('id').encode('utf-8')
		password=self.request.get('password')
		info=get_cookie(id,password)

		try:
			userid = unicode(info['id'],'utf-8')
			newuser=user.get_or_insert(userid, uid=userid)
			date=datetime.fromtimestamp(0)
			newuser.last=datetime.fromtimestamp(0)
			newuser.password=info['password']
			newuser.cookie=info['cookie']
			newuser.err=0
			newuser.put()
			self.response.out.write('ID:%s</br>'%info['id'])
			self.response.out.write('Cookie:%s</br>'%info['cookie'])
			self.response.out.write('Password:%s</br>'%info['password'])
			self.response.out.write('Congratulations, registered successfully!')
		except:
			self.response.out.write('An error occurred, please try again!</br>')
			self.response.out.write('Please check your account and password.')
		
	def get(self):
		self.response.out.write(file("main.html").read())
		
class CronWorkHandler(webapp2.RequestHandler):
    def get(self):
        users=db.GqlQuery("select * from user where last!=NULL ORDER BY last ASC limit 1")
        for auser in users:
            try:
                if auser.last<datetime.fromtimestamp(time.mktime(time.gmtime())+28800).replace(hour=0,minute=0,second=0):
                    id=auser.uid.encode('utf-8')
                    newcookie=get_cookie(id,auser.password)
                    try:
						auser.cookie=newcookie['cookie']
						auser.err=0
						auser.put()
                    except:
						self.response.out.write('%s:Some thing Error.'%auser.uid)
						auser.err+=1
						auser.last=auser.last.replace(second=auser.last.second+1)
						auser.put()
						if auser.err>=5:
							self.response.out.write('will be deleted')
							db.delete(auser)
						return
                    self.response.out.write(id)
                    result=checkin(auser)
                    if result==1:
                        self.response.out.write(' OK')
                    else:
						if result==2:
							self.response.out.write(' Has logged out')
							db.delete(auser)
							return
						else:
							self.response.out.write(result)
							self.response.out.write('Someting Error')
							auser.last=auser.last.replace(second=auser.last.second+1)
							auser.put()
							return 
                    auser.last=datetime.fromtimestamp(time.mktime(time.gmtime())+27000).replace(hour=0,minute=0,second=0)
                    auser.put()
                else:
                    self.response.out.write("Over.")
                return
            except:
                auser.last=auser.last.replace(second=auser.last.second+1)
                auser.put()

    def post(self):
        pass
	
class AllHandler(webapp2.RequestHandler):
	def get(self):
		self.response.out.write("-------All Users-------</br>")
		allusers=db.GqlQuery("SELECT * from user")
		for one in allusers:
			self.response.out.write("uid:%s</br>"%one.uid)
			#self.response.out.write("password:%s</br>"%one.password)
			self.response.out.write("last:%s</br>"%one.last)
			#self.response.out.write("cookie:%s</br>"%one.cookie)
			self.response.out.write("err:%s</br>"%one.err)

	def post(self):
		pass
		
class UpdateHandler(webapp.RequestHandler):

    def get(self):
        alluser=db.GqlQuery("select * from user")
        for auser in alluser:
            auser.err=0
            auser.last=datetime.fromtimestamp(0)
            auser.put()
            self.response.out.write(auser.uid+':'+str(auser.last)+'</br>')

    def post(self):
        pass
app = webapp.WSGIApplication([('/', MainHandler),('/all',AllHandler),('/checkcron',CronWorkHandler),('/upd',UpdateHandler)],debug=True)


def main():
    util.run_wsgi_app(app)


if __name__=="__main__":
    main()
