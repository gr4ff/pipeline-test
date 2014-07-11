import webapp2
import jinja2
import os
import cgi
import time
import urllib
import urllib2
import httplib

import datetime
import logging
import pickle
from google.appengine.api import taskqueue
from google.appengine.api import users
from google.appengine.api import urlfetch
from google.appengine.ext import db
from google.appengine.ext import ndb
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import images
from google.appengine.ext import deferred
from google.appengine.api import mail


jinja_environment = jinja2.Environment(
       loader=jinja2.FileSystemLoader(
           os.path.dirname(__file__)))

class Comment(db.Model):
  content = db.StringProperty(multiline=True)
  date = db.DateTimeProperty(auto_now_add=True)
  moderated = db.DateTimeProperty()
  test123 = db.ListProperty(item_type=int, default=None)

class ProtoT(ndb.Model):
  pikel = ndb.PickleProperty()
  user = ndb.StringProperty()
  data = ndb.DateTimeProperty(auto_now_add=True)

def create_parent_key():
  return db.Key.from_path('ParentKind', 'parentId')


class MainHandler(webapp2.RequestHandler):
  def get(self):
    mail.send_mail(sender="kris@premium-cloud-support.com",
                  to="kmuzyka1@google.com",
                  subject="Your account has been approved",
                  headers={"References": "unique_id"},
                  body="""
    Dear Albert:
    The example.com Team
    """)

    message = mail.EmailMessage(sender="kris@premium-cloud-support.com",
                                subject="Your account has been approved")
    
    message.to = "kmuzyka@google.com"
    message.headers={"References": "unique_id"}
    message.body = """
    Dear Albert:
    
    Your example.com account has been approved.  You can now visit
    http://www.example.com/ and sign in using your Google Account to
    access new features.
    
    Please let us know if you have any questions.
    
    The example.com Team
    """
    self.response.write(str(message.headers)) 
#    self.response.write(template.render(template_data))
#    upload_url = blobstore.create_upload_url('/upload')
#   rows = db.GqlQuery("SELECT * FROM Comment WHERE test123 = NULL")
#   for row in rows:
#     delattr(row, 'test123')
 #    row.test123 = []
#     row.put()
#   for i in range(len(rows)):
#     rows[i].test123 = []
#     rows[i].put()
#   self.response.out.write("done")   
#    self.response.out.write(str(images.IMG_SERVING_SIZES_LIMIT))
#    self.response.out.write('<html><body>')
#    self.response.out.write('<form action="%s" method="POST" enctype="multipart/form-data">' % upload_url)
#    self.response.out.write("""Upload File: <input type="file" name="file"><br> <input type="submit"
#      name="submit" value="Submit"> </form></body></html>""")


class SendHandler(webapp2.RequestHandler):
  def post(self):
    comment = Comment(parent=create_parent_key())
    comment.content = self.request.get('comment')
    comment.test123 = None
    comment.put()
    taskqueue.add(url='/worker')
    self.redirect('/')

    
class Worker(webapp2.RequestHandler):
  def post(self):
    # We could do some useful work here.
    # For now, let's pretend by sleeping.
    time.sleep(30)
    comments = db.GqlQuery('SELECT * FROM Comment')
    for comment in comments:
      comment.moderated = datetime.datetime.now()
      comment.put()

@ndb.tasklet
def get_google():
  ctx = ndb.get_context()
  result = yield ctx.urlfetch('http://fake-response.appspot.com/?sleep=120', deadline=200)
  if result.status_code == 200:
    raise ndb.Return(result.content)

def doAsyncFetch():
  rpc = urlfetch.create_rpc(deadline=120) # 1 second deadline. 
  urlfetch.make_fetch_call(rpc, 'http://fake-response.appspot.com/?sleep=110')
  logging.info('doing nothing')
  time.sleep(90)
  result = rpc.get_result() # Throws error here. 
  logging.info(result.status_code)

def do_normal_fetch():
  result = urlfetch.fetch(url='https://lh3.ggpht.com/HlbchxHScJzGEjmQ3nlDTVsUsqGfwnNRmRH4dQi_YUiR16K1g1O6Bqf6dXW89ygEWuTyhqlASNlE5MISJiyHvUbS', 
    deadline=5, validate_certificate=True)
#  result = urllib2.urlopen('http://channel.api.duapp.com/rest/2.0/channel/channel')
#  conn = httplib.HTTPConnection("channel.api.duapp.com")
#  conn.request("GET", "/index.html")
#  result = conn.getresponse()
  logging.info(str(result))


class RpcAsync(webapp2.RequestHandler):
  def get(self):
#    result = urlfetch.fetch(url='http://fake-response.appspot.com/?sleep=110', deadline=120)
#    logging.info(result.status_code)
    do_normal_fetch()
#    deferred.defer(do_normal_fetch, _queue="default")

class QueueRpcAsync(webapp2.RequestHandler):
  def get(self):
    taskqueue.add(url='/async',  method='GET')


class MainHandler1(webapp2.RequestHandler):
  def get(self):
    upload_url = blobstore.create_upload_url('/upload', gs_bucket_name='kris-molly')
    #### remove!!!!
    upload_url = '/serve1'
    ######
    self.response.out.write('<html><body>')
    self.response.out.write('<form action="%s" method="POST" enctype="multipart/form-data">' % upload_url)
    self.response.out.write("""Upload File: <input type="file" name="file"><br> <input type="submit"
        name="submit" value="Submit"> </form></body></html>""")


class UploadHandler1(blobstore_handlers.BlobstoreUploadHandler):
  def post(self):
    upload_files = self.get_uploads('file')  # 'file' is file upload field in the form
    blob_info = upload_files[0]
    self.response.out.write("2222" + str(self.get_file_infos('file')[0].gs_object_name))


class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
  def post(self):
    upload_files = self.get_uploads('file')  # 'file' is file upload field in the form
#    self.response.write(cgi.escape(self.request.get('comment')))
    blob_info = upload_files[0]
    self.redirect('/serve/%s' % blob_info.key())


class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
  def get(self, resource):
    resource = str(urllib.unquote(resource))
    blob_info = blobstore.BlobInfo.get(resource)
#    blob_info = images.get_serving_url(blobstore.BlobInfo.get(resource))
    self.response.out.write(str(blob_info))
    self.response.out.write("3333" + str(blob_info.filename))
    blob_reader = blobstore.BlobReader(blob_info.key())
    data = blob_reader.read(100)

    self.response.out.write(str(data))

class ServeHandler1(webapp2.RequestHandler):
  def post(self):
    self.response.out.write(str(self.request.get('file')))

class MainHandlerE(webapp2.RequestHandler):
  def get(self):
    upload_url = blobstore.create_upload_url('/eupload')
    self.response.out.write('<html><body>')
    self.response.out.write('<form action="%s" method="POST" enctype="multipart/form-data">' % upload_url)
    self.response.out.write("""Upload File: <input type="file" name="file"><br> <input type="submit"
        name="submit" value="Submit"> </form></body></html>""")

class UploadHandlerE(blobstore_handlers.BlobstoreUploadHandler):
  def post(self):
    upload_files = self.get_uploads('file')  # 'file' is file upload field in the form
    blob_info = upload_files[0]
    self.redirect('/serve/%s' % blob_info.key())

class ServeHandlerE(blobstore_handlers.BlobstoreDownloadHandler):
  def get(self, resource):
    resource = str(urllib.unquote(resource))
    blob_info = blobstore.BlobInfo.get(resource)
    self.send_blob(blob_info)

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/send', SendHandler),
    ('/async', RpcAsync),
    ('/doasync', QueueRpcAsync),
    ('/serve/([^/]+)?', ServeHandler),
    ('/upload', UploadHandler),
    ('/worker', Worker),
    ('/modupl', MainHandler1),
    ('/serve1', ServeHandler1),
    ('/e', MainHandlerE),
    ('/eupload', UploadHandlerE),
    ('/eserve/([^/]+)?', ServeHandlerE)
], debug=True)
