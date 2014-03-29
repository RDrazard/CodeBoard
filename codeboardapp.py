#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import uuid
import bottle
import pymongo
from libs import oauth2client

bottle.debug(True)

client = pymongo.MongoClient('localhost', 27017)

mongo_db = client.codeboard
mongo_db.authenticate(os.environ['OPENSHIFT_MONGODB_DB_USERNAME'],
                      os.environ['OPENSHIFT_MONGODB_DB_PASSWORD'])

def user_find(userid):
  if not userid: return None
  return mongo_db.users.find_one({ '_id': userid})

def user_create(username, password):
  if not username: return None
  # check for pre existance
  tuser = user_find(username)
  if tuser: return None

  nuser = {
    '_id': username,
    'pw': password
    }
  userid = mongo_db.users.insert(nuser)
  return userid

def snippet_create(user, code):
  nsnippet = {
    '_id': uuid.uuid4().hex,
    'uid': user['_id'],
    'code': snippet,
    }
  mongo_db.snippets.insert(nsnippet)

def note_create(snip, user, text):
  nnote = {
    '_id': uuid.uuid4().hex,
    'uid': user['_id'],
    'cid': snip['_id'],
    'text': text
  }
  mongo_db.notes.insert(nnote)

def annote_create(snip, user, text):
  nannote = {
    '_id': uuid.uuid4().hex,
    'uid': user['_id'],
    'cid': snip['_id'],
    'text': text
  }
  mongo_db.notes.insert(nannote)

def user_list():
  l = []
  for u in mongo_db.users.find():
    l.append(u['_id'])
  l.sort()
  return l

def snippet_list(user):
  l = []
  for s in mongo_db.snippets.find():
      if s['uid'] == user:
        l.append(s)
  l.sort()
  return l

def note_list(snippet):
  l = []
  for n in mongo_db.notes.find():
    if n['cid'] == snippet:
      l.append(n)
  l.sort()
  return l

def annote_list(snippet):
  l = []
  for a in mongo_db.annotes.find():
    if a['cid'] == snippet:
      l.append(a)
  l.sort()
  return l

def user_auth(user, pw):
  # if not user: return False
  # return user['pw'] == pw

def snippet_find_by_id(post_id):
  if not post_id: return None
  return mongo_db.posts.find_one({ '_id': post_id})

reserved_usernames = 'home signup login logout post static DEBUG note annote'

bottle.TEMPLATE_PATH.append(os.path.join(os.environ['OPENSHIFT_REPO_DIR'],
                                          'views'))

def get_session():
  session = bottle.request.get_cookie('session', secret='secret')
  return session;

def save_session(uid):
  session = {}
  session['uid'] = uid
  session['sid'] = uuid.uuid4().hex
  bottle.response.set_cookie('session', session, secret='secret')
  return session;

def invalidate_session():
  bottle.response.delete_cookie('session', secret='secret')
  return

@bottle.route('/', method="GET")
def index():
  # Create a state token to prevent request forgery.
  # Store it in the session for later validation.
  state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                  for x in range(32))
  session['state'] = state
  # Set the Client ID, Token State, and Application Name in the HTML while
  # serving it.
  response = make_response(
      render_template('index.html',
                      CLIENT_ID='604107449096-1d5g1d4g8h071vlstohq6c73i2q4acoj.apps.googleusercontent.com',
                      STATE=state,
                      APPLICATION_NAME='CodeBoard'))

  session = get_session()
  if session:
    bottle.redirect('/home')
  return bottle.template('home_not_logged',
                         logged=False)

@bottle.route('/oauth2callback', method="POST"):
def connect():
  # Ensure that the request is not a forgery and that the user sending
  # this connect request is the expected user.
  if request.args.get('state', '') != session['state']:
    response = make_response(json.dumps('Invalid state parameter.'), 401)
    response.headers['Content-Type'] = 'application/json'
  return response

  del session['state']

  gplus_id = request.args.get('gplus_id')
  code = request.data

  try:
    # Upgrade the authorization code into a credentials object
    oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
    oauth_flow.redirect_uri = 'postmessage'
    credentials = oauth_flow.step2_exchange(code)
  except FlowExchangeError:
    response = make_response(
        json.dumps('Failed to upgrade the authorization code.'), 401)
    response.headers['Content-Type'] = 'application/json'
    return response

  # Check that the access token is valid.
  access_token = credentials.access_token
  url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
         % access_token)
  h = httplib2.Http()
  result = json.loads(h.request(url, 'GET')[1])
  # If there was an error in the access token info, abort.
  if result.get('error') is not None:
    response = make_response(json.dumps(result.get('error')), 500)
    response.headers['Content-Type'] = 'application/json'
    return response
  # Verify that the access token is used for the intended user.
  if result['user_id'] != gplus_id:
    response = make_response(
        json.dumps("Token's user ID doesn't match given user ID."), 401)
    response.headers['Content-Type'] = 'application/json'
    return response
  # Verify that the access token is valid for this app.
  if result['issued_to'] != CLIENT_ID:
    response = make_response(
        json.dumps("Token's client ID does not match app's."), 401)
    response.headers['Content-Type'] = 'application/json'
    return response
  stored_credentials = session.get('credentials')
  stored_gplus_id = session.get('gplus_id')
  if stored_credentials is not None and gplus_id == stored_gplus_id:
    response = make_response(json.dumps('Current user is already connected.'),
                             200)
    response.headers['Content-Type'] = 'application/json'
    return response
  # Store the access token in the session for later use.
  session['credentials'] = credentials
  session['gplus_id'] = gplus_id
  response = make_response(json.dumps('Successfully connected user.', 200))

@bottle.route('/home')
def home():
  session = get_session()
  if not session: bottle.redirect('/login')
  luser = user_find(session['uid'])
  if not luser: bottle.redirect('/logout')
  
  # bottle.TEMPLATES.clear()
  return bottle.template('timeline',
                         postlist=postlist,
                         userlist=user_list(),
                         page='timeline',
                         username=luser['_id'],
                         logged=True)

@bottle.route('/<name>')
def user_page(name):
  session = get_session()
  luser = user_find(session['uid'])
  if not luser: bottle.redirect('/logout')
  tuser = user_find(name)
  if not tuser: return bottle.HTTPError(code=404)
  himself = session['uid'] == tuser['_id']
  
  # bottle.TEMPLATES.clear()
  return bottle.template('user',
                         page='user',
                         username=tuser['_id'],
                         logged=True,
                         himself=himself)

@bottle.route('/<name>/snippets')
def snippet_page(name):
    session = get_session()
    luser = user_find(session['uid'])
    if not luser: bottle.redirect('/logout')
    tuser = user_find(name)

    return bottle.template('snippets',
                            snippet_list=snippet_list(),
                            page='snippets',
                            username=tuser['_id'])
  
@bottle.route('/<name>/snippets/<id>')
def board(name,id):
  session = get_session()
  snippet = snippet_find_by_id(id)
  if not snippet:
    return bottle.HTTPError(code=404, message='snippet not found')
  return bottle.template('snip',
                         username=post['uid'],
                         snip_id=id,
                         code=post['code'],
                         page='snip',
                         annotes=annote_list(snippet)
                         notes=note_list(snippet)
                         logged=(session != None))

@bottle.route('/note/<snip>', method='POST')
def note(snip):
  session = get_session()
  if not session: bottle.redirect('/login')
  luser = user_find(session['uid'])
  if not luser: bottle.redirect('/logout')
  if 'text' in bottle.request.POST:
    text = bottle.request.POST['text']
    note_create(snip, luser, text)

@bottle.route('/annote/<snip>', method='POST')
def annote(snip):
  session = get_session()
  if not session: bottle.redirect('/login')
  luser = user_find(session['uid'])
  if not luser: bottle.redirect('/logout')
  if 'text' in bottle.request.POST:
    text = bottle.request.POST['text']
    annote_create(snip, luser, text)

# def get_login():
#   session = get_session()
#   # bottle.TEMPLATES.clear()
#   if session: bottle.redirect('/home')
#   return bottle.template('login',
# 			 page='login',
# 			 error_login=False,
# 			 error_signup=False,
# 			 logged=False)

@bottle.route('/oauth2callback', method='POST')
def post_login():
  if 'email' in bottle.request.POST and 'token' in bottle.request.POST:
    email = bottle.request.POST['email']
    user = user_find(email)
    if user_auth(email, token):
      save_session(user['_id'])
      bottle.redirect('/home')
  return bottle.template('login',
			 page='login',
			 error_login=True,
			 error_signup=False,
			 logged=False)

@bottle.route('/logout')
def logout():
  invalidate_session()
  bottle.redirect('/')

@bottle.route('/signup', method='POST')
def post_signup():
  if 'name' in bottle.request.POST and 'password' in bottle.request.POST:
    name = bottle.request.POST['name']
    password = bottle.request.POST['password']
    if name not in reserved_usernames.split():
      userid = user_create(name, password)
      if userid:
        save_session(userid)
        bottle.redirect('/home')
    return bottle.template('login',
			   page='login',
			   error_login=False,
			   error_signup=True,
			   logged=False)

@bottle.route('/DEBUG/cwd')
def dbg_cwd():
  return "<tt>cwd is %s</tt>" % os.getcwd()

@bottle.route('/DEBUG/env')
def dbg_env():
  env_list = ['%s: %s' % (key, value)
              for key, value in sorted(os.environ.items())]
  return "<pre>env is\n%s</pre>" % '\n'.join(env_list)

@bottle.route('/static/:filename')
def static_file(filename):
  bottle.send_file(filename,
                   root= os.path.join(os.environ['OPENSHIFT_REPO_DIR'],
                                      'static'))

application = bottle.default_app()
