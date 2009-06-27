
from oauth import oauth
from oauth.oauth import OAuthRequest, OAuthToken
import urllib2
import cgi
import time
from datetime import datetime
from urllib import urlencode, quote
try:
    import json
except ImportError:
    import simplejson as json
import logging

logging.basicConfig(level=logging.DEBUG,)

class NotFound(Exception):
    pass

class NetflixObject(object):
    def get(self, netflix=None, token=None, key=None, secret=None):
        if not netflix:
            netflix = Netflix(key=key, secret=secret)
        return netflix.request(self, token=token)

class Printable(object):
    def __str__(self):
        return self._imp

    @property
    def _imp(self):
        important = getattr(self, 'important')
        try:
            return getattr(self, important)
        except TypeError:
            return getattr(self, important[0])

    def __repr__(self):
        if isinstance(self.important, (tuple, list)):
            data =  ', '.join("%r" % getattr(self, k) for k in self.important)
        else:
            data = "%r" % getattr(self, self.important)

        return "<%s %s>" % (type(self).__name__, data)

    def __getattr__(self, name):
        return getattr(self._imp, name)

    def __getitem__(self, key):
        return self._imp.__getitem__(key)

    def __add__(self, other):
        return self._imp + other

    def __radd__(self, other):
        return self + other

class NetflixLink(NetflixObject, Printable):
    important = 'href'
    def __init__(self, href=None, rel=None, title=None):
        self.href, self.rel, self.title = href, rel, title

class NetflixCategory(NetflixObject, Printable):
    important = 'term'
    def __init__(self, label=None, scheme=None, term=None):
        self.label, self.scheme, self.term = label, scheme, term

class FancyObject(NetflixObject):
    def __init__(self, d):
        self.links = dict((di['title'], NetflixLink(**di)) for di in d.pop('link'))
        for k in d:
            setattr(self, k, d[k])


class CatalogTitle(FancyObject, Printable):
    important = ('title', 'id')
    def __init__(self, d):
        title = d.pop('title')
        self.title = title['regular']
        self.title_short = title['short']
        self.categories = [NetflixCategory(**di) for di in d.pop('category')]
        super(CatalogTitle, self).__init__(d)

class NetflixUser(FancyObject, Printable):
    important = ('last_name', 'first_name', 'user_id')

    def __init__(self, d):
        preferred_formats = d.pop('preferred_formats')
        if not isinstance(preferred_formats, (list, tuple)):
            preferred_formats = [preferred_formats]
        self.preferred_formats = [NetflixCategory(**dd['category']) for dd in preferred_formats]
        super(NetflixUser, self).__init__(d)

class RentalHistory(FancyObject):
    def __init__(self, d):
        self.items = [CatalogTitle(dd) for dd in d.pop('rental_history_item')]
        super(RentalHistory, self).__init__(d)

class NetflixAvailability(NetflixObject, Printable):
    important = ('category', 'available_from')
    def __init__(self, d):
        self.category = NetflixCategory(**d['category'])
        try:
            self.available_from = datetime.fromtimestamp(float(d['available_from']))
            self.available = False
        except KeyError:
            self.available_from = None
        try:
            self.available_until = datetime.fromtimestamp(float(d['available_until']))
        except KeyError:
            self.available_until = None

class Netflix(object):
    protocol = "http://"
    host = 'api.netflix.com'
    port = '80'
    request_token_url = 'http://api.netflix.com/oauth/request_token'
    access_token_url  = 'http://api.netflix.com/oauth/access_token'
    authorization_url = 'https://api-user.netflix.com/oauth/login'
    signature_method = oauth.OAuthSignatureMethod_HMAC_SHA1()

    def __init__(self, key, secret, application_name=None):
        self.consumer = oauth.OAuthConsumer(key, secret)
        self.application_name = application_name

    def object_hook(self, d):
        d = dict((str(k), v) for k, v in d.iteritems())

        def isa(label):
            return label in d and len(d) == 1

        if 'catalog_titles' in d:
            try:
                return [CatalogTitle(di) for di in d['catalog_titles']['catalog_title']]
            except (KeyError, TypeError):
                return d['catalog_titles']
        elif isa('catalog_title'):
            try:
                return CatalogTitle(d['catalog_title'])
            except TypeError:
                return [CatalogTitle(i) for i in d['catalog_title']]
        elif isa('synopsis'):
            return d['synopsis']
        elif isa('delivery_formats'):
            availabilities = d['delivery_formats']['availability']
            if not isinstance(availabilities, list):
                availabilities = [availabilities]
            return [NetflixAvailability(o) for o in availabilities]
        elif isa('user'):
            return NetflixUser(d['user'])
        elif isa('rental_history'):
            return RentalHistory(d['rental_history'])
        else:
            return d

    def get_request_token(self):
        oa_req = OAuthRequest.from_consumer_and_token(
            self.consumer,
            http_url=self.request_token_url)
        oa_req.sign_request(self.signature_method,
                                  self.consumer,
                                  None)
        req = urllib2.Request(
            self.request_token_url,
            headers = oa_req.to_header())
        request_token = OAuthToken.from_string(urllib2.urlopen(req).read())
        return request_token

    def get_authorization_url(self, callback=None):
        """Return the authorization url and token."""
        token = self.get_request_token()
        parameters = dict(application_name=self.application_name)
        if callback:
            parameters['oauth_callback'] = callback
        oauth_request = OAuthRequest.from_consumer_and_token(
            self.consumer,
            token=token,
            parameters=parameters,
            http_url=self.authorization_url,
        )
        oauth_request.sign_request(self.signature_method, self.consumer, token)
        return oauth_request.to_url(), token

    def authorize(self, token):
        """Authorize a user with netflix and return a user id and an
        access token."""
        oa_req = OAuthRequest.from_consumer_and_token(
            self.consumer,
            token=token,
            parameters={'application_name': self.application_name} if self.application_name else None,
            http_url=self.access_token_url
        )

        oa_req.sign_request(
            self.signature_method,
            self.consumer,
            token
        )
        try:
            req = urllib2.urlopen(oa_req.to_url())
        except urllib2.HTTPError,e:
            # todo: someting better here
            raise
        res = req.read()
        logging.debug(res)
        id = cgi.parse_qs(res)['user_id'][0]

        return id, OAuthToken.from_string(res)


    def request(self, url, token=None, **args):
        """`url` may be relative with regard to Netflix.

        """
        if not url.startswith('http://'):
            url = self.protocol + self.host + url
        args['output'] = 'json'
        oa_req = OAuthRequest.from_consumer_and_token(self.consumer,
                                                            http_url=url,
                                                            parameters=args,
                                                            token=token)
        oa_req.sign_request(self.signature_method,
                            self.consumer,
                            token)
        try:
            req = urllib2.urlopen(oa_req.to_url())
        except urllib2.HTTPError, e:
            logging.debug("We got an http error: %s" % e)
            try:
                time.sleep(1)
                req = urllib2.urlopen(oa_req.to_url())
            except urllib2.HTTPError, e:
                raise NotFound(url, e)
        return json.load(req, object_hook=self.object_hook)
