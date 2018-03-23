from google.appengine.ext.webapp import template
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
import webapp2
import json
import os
import urllib
import random
import string
import sys

CLIENT_ID = '698911262591-h26odkjcc3gb4pvtuhju2mu2nr1m5q7i.apps.googleusercontent.com'
SECRET = 'K4wEgcTOl22vlqdUX9pyKfXh'
REDIRECT = 'https://assignment3-496.appspot.com/oauth'
#random string from: https://pythontips.com/2013/07/28/generating-a-random-string/
STATE_STRING = ''.join([random.choice(string.ascii_letters + string.digits) for i in xrange(32)])

class userAccount(ndb.Model):
    id = ndb.StringProperty()
    fname = ndb.StringProperty()
    lname = ndb.StringProperty()
    email = ndb.StringProperty()
    userID = ndb.StringProperty()

class Book(ndb.Model):
    id = ndb.StringProperty()
    author = ndb.StringProperty()
    title = ndb.StringProperty()
    userID = ndb.StringProperty()
    review = ndb.StringProperty()
    yearPub = ndb.IntegerProperty()

class MainPage(webapp2.RequestHandler):
    def get(self):
        siteUrl = 'https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id='
        siteUrl = siteUrl + CLIENT_ID
        siteUrl = siteUrl + '&redirect_uri=' + REDIRECT
        siteUrl = siteUrl + '&scope=email&state=' + STATE_STRING
        #self.response.write(siteUrl)

#using the template to get the url on the site from http://webapp2.readthedocs.io/en/latest/tutorials/gettingstarted/templates.html
        template_values = {
            'url': siteUrl,
            'url_linktext': 'Click This',
        }
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.write(template.render(path, template_values))

class OauthHandler(webapp2.RequestHandler):
    def get(self):
        gotCode = self.request.GET['code']
        ourState = STATE_STRING
        theirState = self.request.GET['state']
        #confirm the state is the same
        if(ourState != theirState):
            sys.exit("We have the wrong state")
        #else:
        #    self.response.write("So far so good.")
        #using https://stackoverflow.com/questions/19102927/how-to-make-a-post-request-in-python-and-webapp2 to help
        post = {
            'code': gotCode,
            'client_secret': SECRET,
            'client_id': CLIENT_ID,
            'redirect_uri': REDIRECT,
            'grant_type': 'authorization_code'
        }
        load = urllib.urlencode(post)
        #using https://cloud.google.com/appengine/docs/standard/python/issue-requests to help
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        #url gotten from assignment lectures
        response = urlfetch.fetch(
            url = "https://www.googleapis.com/oauth2/v4/token",
            payload = load,
            method = urlfetch.POST,
            headers = headers
        )
        #self.response.write(response.content)
        #move to json to get at the token
        postResult = json.loads(response.content)
        token = postResult['access_token']
        #header and url info from lecture video
        header = {'Authorization': 'Bearer ' + token}
        newResponse = urlfetch.fetch(
            url = "https://www.googleapis.com/plus/v1/people/me",
            method = urlfetch.GET,
            headers = header
        )
        #self.response.write(newResponse.content)
        newResult = json.loads(newResponse.content)
        #so now we should have user information
        #need to string the url for it to work
        firstName = newResult['name']['givenName']
        lastName = newResult['name']['familyName']
        email = newResult['emails'][0]['value']
        #need to template for the next page to get the info back to them.
        template_values = {
            'first': firstName,
            'last': lastName,
            'email': email,
            'token': 'Bearer ' + token
        }

        #now we have the information we need to create a userAccount!
        #check if that account exists
        #userExists = False
        #userQuery = userAccount.query()
        #for user in userQuery:
        #    if user.userID == userID:
        #        userExists = True

        #if not userExists:
        #    newUser = userAccount()
        #    newUser.fname = firstName
        #    newUser.lname = lastName
        #    newUser.email = email
        #    newUser.userID = userID
        #    newUser.put()
        #    newUser.id = str(newUser.key.urlsafe())
        #    newUser.put()

        path = os.path.join(os.path.dirname(__file__), 'oauth.html')
        self.response.write(template.render(path, template_values))

class UserHandler(webapp2.RequestHandler):
    def post(self):
        header = self.request.headers
        newResponse = urlfetch.fetch(
            url = "https://www.googleapis.com/plus/v1/people/me",
            method = urlfetch.GET,
            headers = header
        )
        #self.response.write(newResponse.content)
        newResult = json.loads(newResponse.content)
        userID = newResult['id']
        userExists = False
        userQuery = userAccount.query()
        for user in userQuery:
            if user.userID == userID:
                userExists = True
        postData = json.loads(self.request.body)
        if not userExists:
            newUser = userAccount(fname=postData['first'], lname=postData['last'], email=postData['email'])
            newUser.put()
            newUser.userID = userID
            newUser.put()
            newUser.id = str(newUser.key.urlsafe())
            newUser.put()
            userDict = newUser.to_dict()
            self.response.write(json.dumps(userDict))
        else:
            self.response.write("User already exists!")

    def get(self):
        header = self.request.headers
        newResponse = urlfetch.fetch(
            url = "https://www.googleapis.com/plus/v1/people/me",
            method = urlfetch.GET,
            headers = header
        )
        #self.response.write(newResponse.content)
        newResult = json.loads(newResponse.content)
        userID = newResult['id']
        userExists = False
        accountKey = ""
        for user in userAccount.query():
            if user.userID == userID:
                userExists = True
                accountKey = user.id
                user = ndb.Key(urlsafe=accountKey).get()
                user_dict = user.to_dict()
                self.response.write(json.dumps(user_dict))
        if not userExists:
            self.response.status = 400
            self.response.write("ERROR: User does not exist!")

    def put(self):
        #make put (edit everything)
        header = self.request.headers
        newResponse = urlfetch.fetch(
            url = "https://www.googleapis.com/plus/v1/people/me",
            method = urlfetch.GET,
            headers = header
        )
        #self.response.write(newResponse.content)
        newResult = json.loads(newResponse.content)
        userID = newResult['id']
        userExists = False
        userIDkey = ""
        editData = json.loads(self.request.body)
        for user in userAccount.query():
            if user.userID == userID:
                userExists = True
                userIDkey = user.id
        if userExists:
            userToEdit = ndb.Key(urlsafe=userIDkey).get()
            newFirst = False
            newLast = False
            newEmail = False
            for item in editData:
                if item == "first":
                    newFirst = True
                elif item == "last":
                    newLast = True
                elif item == "email":
                    newEmail = True
            if newFirst and newLast and newEmail and (len(editData) == 3):
                userToEdit.fname = editData['first']
                userToEdit.lname = editData['last']
                userToEdit.email = editData['email']
                userToEdit.put()
                user_dict = userToEdit.to_dict()
                self.response.write(json.dumps(user_dict))
            else:
                self.response.status = 400
                self.response.write("ERROR: Please edit all 3 properties at once.")
        else:
            self.response.status = 400
            self.response.write("ERROR: User does not exist!")

    def patch(self):
        #make patch (edit 1 thing)
        header = self.request.headers
        newResponse = urlfetch.fetch(
            url = "https://www.googleapis.com/plus/v1/people/me",
            method = urlfetch.GET,
            headers = header
        )
        #self.response.write(newResponse.content)
        newResult = json.loads(newResponse.content)
        userID = newResult['id']
        userExists = False
        userIDkey = ""
        editData = json.loads(self.request.body)
        for user in userAccount.query():
            if user.userID == userID:
                userExists = True
                userIDkey = user.id
        if userExists:
            userToEdit = ndb.Key(urlsafe=userIDkey).get()
            if len(editData) == 1:
                for item in editData:
                    if item == "first":
                        userToEdit.fname = editData['first']
                        userToEdit.put()
                        user_dict = userToEdit.to_dict()
                        self.response.write(json.dumps(user_dict))
                    if item == "last":
                        userToEdit.lname = editData['last']
                        userToEdit.put()
                        user_dict = userToEdit.to_dict()
                        self.response.write(json.dumps(user_dict))
                    if item == "email":
                        userToEdit.email = editData['email']
                        userToEdit.put()
                        user_dict = userToEdit.to_dict()
                        self.response.write(json.dumps(user_dict))
            else:
                self.response.status = 400
                self.response.write("ERROR: Please edit one property at a time!")
        else:
            self.response.status = 400
            self.response.write("ERROR: User does not exist!")

    def delete(self):
        #delete user and all associated books
        header = self.request.headers
        newResponse = urlfetch.fetch(
            url = "https://www.googleapis.com/plus/v1/people/me",
            method = urlfetch.GET,
            headers = header
        )
        #self.response.write(newResponse.content)
        newResult = json.loads(newResponse.content)
        userID = newResult['id']
        userExists = False
        userIDkey = ""
        bookKey = ""
        for user in userAccount.query():
            if user.userID == userID:
                userExists = True
                userIDkey = user.id
        if userExists:
            userToDelete = ndb.Key(urlsafe=userIDkey).get()
            for book in Book.query():
                if userToDelete.userID == book.userID:
                    bookKey = book.id
                    bookToDelete = ndb.Key(urlsafe=bookKey).get()
                    bookToDelete.key.delete()
            userToDelete.key.delete()
            self.response.write("User and all associated books deleted.")
        else:
            self.response.status = 400
            self.response.write("ERROR: User does not exist!")

class BookAddHandler(webapp2.RequestHandler):
    def get(self):
        header = self.request.headers
        newResponse = urlfetch.fetch(
            url = "https://www.googleapis.com/plus/v1/people/me",
            method = urlfetch.GET,
            headers = header
        )
        #self.response.write(newResponse.content)
        newResult = json.loads(newResponse.content)
        userID = newResult['id']
        userExists = False
        bookExists = False
        bookList = []
        for user in userAccount.query():
            if user.userID == userID:
                userExists = True
        if userExists:
            for book in Book.query():
                if userID == book.userID:
                    bookExists = True
                    bookDict = book.to_dict()
                    bookList.append(bookDict)
            if bookExists:
                self.response.write(json.dumps(bookList))
            else:
                self.response.status = 400
                self.response.write("ERROR: User has no books.")
        else:
            self.response.status = 400
            self.response.write("ERROR: User does not exist.")

    def post(self):
        header = self.request.headers
        newResponse = urlfetch.fetch(
            url = "https://www.googleapis.com/plus/v1/people/me",
            method = urlfetch.GET,
            headers = header
        )
        #self.response.write(newResponse.content)
        newResult = json.loads(newResponse.content)
        userID = newResult['id']
        userExists = False
        for user in userAccount.query():
            if user.userID == userID:
                userExists = True
        if userExists:
            bookData = json.loads(self.request.body)
            newBook = Book(title=bookData['title'], author=bookData['author'], yearPub=bookData['published'], review=bookData['review'])
            newBook.put()
            newBook.userID = userID
            newBook.put()
            newBook.id = newBook.key.urlsafe()
            newBook.put()
            bookDict = newBook.to_dict()
            self.response.write(json.dumps(bookDict))
        else:
            self.response.status = 400
            self.response.write("ERROR: User does not exist.")

class BookEditHandler(webapp2.RequestHandler):
    def get(self, bookID):
        header = self.request.headers
        newResponse = urlfetch.fetch(
            url = "https://www.googleapis.com/plus/v1/people/me",
            method = urlfetch.GET,
            headers = header
        )
        #self.response.write(newResponse.content)
        newResult = json.loads(newResponse.content)
        userID = newResult['id']
        userExists = False
        bookExists = False
        for user in userAccount.query():
            if user.userID == userID:
                userExists = True
        if userExists:
            for book in Book.query():
                if book.id == bookID:
                    bookExists = True
            if bookExists:
                book = ndb.Key(urlsafe=bookID).get()
                bookDict = book.to_dict()
                self.response.write(json.dumps(bookDict))
            else:
                self.response.status = 400
                self.response.write("ERROR: Book does not exist!")
        else:
            self.response.status = 400
            self.response.write("ERROR: User does not exist!")

    def put(self, bookID):
        #used to edit everything about a book except IDs
        header = self.request.headers
        newResponse = urlfetch.fetch(
            url = "https://www.googleapis.com/plus/v1/people/me",
            method = urlfetch.GET,
            headers = header
        )
        #self.response.write(newResponse.content)
        newResult = json.loads(newResponse.content)
        userID = newResult['id']
        userExists = False
        bookExists = False
        editData = json.loads(self.request.body)
        for user in userAccount.query():
            if user.userID == userID:
                userExists = True
        if userExists:
            for book in Book.query():
                if book.id == bookID:
                    bookExists = True
            if bookExists:
                bookToEdit = ndb.Key(urlsafe=bookID).get()
                newTitle = False
                newAuthor = False
                newReview = False
                newPub = False
                for item in editData:
                    if item == "title":
                        newTitle = True
                    elif item == "author":
                        newAuthor = True
                    elif item == "review":
                        newReview = True
                    elif item == "published":
                        newPub = True
                if newPub and newReview and newTitle and newAuthor and (len(editData) == 4):
                    bookToEdit.title = editData['title']
                    bookToEdit.author = editData['author']
                    bookToEdit.yearPub = editData['published']
                    bookToEdit.review = editData['review']
                    bookToEdit.put()
                    bookDict = bookToEdit.to_dict()
                    self.response.write(json.dumps(bookDict))
                else:
                    self.response.status = 400
                    self.response.write("ERROR: Please edit all 4 properties at once.")
            else:
                self.response.status = 400
                self.response.write("ERROR: Book does not exist!")
        else:
            self.response.status = 400
            self.response.write("ERROR: User does not exist!")

    def patch(self, bookID):
        #used to edit 1 property of a book.
        header = self.request.headers
        newResponse = urlfetch.fetch(
            url = "https://www.googleapis.com/plus/v1/people/me",
            method = urlfetch.GET,
            headers = header
        )
        #self.response.write(newResponse.content)
        newResult = json.loads(newResponse.content)
        userID = newResult['id']
        userExists = False
        bookExists = False
        editData = json.loads(self.request.body)
        for user in userAccount.query():
            if user.userID == userID:
                userExists = True
        if userExists:
            for book in Book.query():
                if book.id == bookID:
                    bookExists = True
            if bookExists:
                bookToEdit = ndb.Key(urlsafe=bookID).get()
                if len(editData) == 1:
                    for item in editData:
                        if item == "title":
                            bookToEdit.title = editData['title']
                            bookToEdit.put()
                            bookDict = bookToEdit.to_dict()
                            self.response.write(json.dumps(bookDict))
                        if item == "author":
                            bookToEdit.author = editData['author']
                            bookToEdit.put()
                            bookDict = bookToEdit.to_dict()
                            self.response.write(json.dumps(bookDict))
                        if item == "published":
                            bookToEdit.yearPub = editData['published']
                            bookToEdit.put()
                            bookDict = bookToEdit.to_dict()
                            self.response.write(json.dumps(bookDict))
                        if item == "review":
                            bookToEdit.review = editData['review']
                            bookToEdit.put()
                            bookDict = bookToEdit.to_dict()
                            self.response.write(json.dumps(bookDict))
                else:
                    self.response.status = 400
                    self.response.write("ERROR: Please edit one property at a time!")
            else:
                self.response.status = 400
                self.response.write("ERROR: Book does not exist!")
        else:
            self.response.status = 400
            self.response.write("ERROR: User does not exist!")

    def delete(self, bookID):
        header = self.request.headers
        newResponse = urlfetch.fetch(
            url = "https://www.googleapis.com/plus/v1/people/me",
            method = urlfetch.GET,
            headers = header
        )
        #self.response.write(newResponse.content)
        newResult = json.loads(newResponse.content)
        userID = newResult['id']
        userExists = False
        bookExists = False
        for user in userAccount.query():
            if user.userID == userID:
                userExists = True
        if userExists:
            for book in Book.query():
                if book.id == bookID:
                    bookExists = True
            if bookExists:
                book = ndb.Key(urlsafe=bookID).get()
                book.key.delete()
                self.response.write("Book Succesfully deleted!")
            else:
                self.response.status = 400
                self.response.write("ERROR: Book does not exist!")
        else:
            self.response.status = 400
            self.response.write("ERROR: User does not exist!")

allowed_methods = webapp2.WSGIApplication.allowed_methods
new_allowed_methods = allowed_methods.union(('PATCH',))
webapp2.WSGIApplication.allowed_methods = new_allowed_methods
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/oauth', OauthHandler),
    ('/user', UserHandler),
    ('/bookadd', BookAddHandler),
    ('/bookedit/(.*)', BookEditHandler),
], debug=True)
