
from oauth import oauth
from oauth.oauth import OAuthRequest, OAuthToken
import urllib2
import cgi
import time
from datetime import datetime
from urllib import urlencode, quote
import urllib3
try:
    import json
except ImportError:
    import simplejson as json
import logging

from interval import call_interval

logging.basicConfig(level=logging.DEBUG,)

class NetflixError(Exception):
    pass

class NotFound(NetflixError):
    pass

class AuthError(NetflixError):
    pass

class InvalidSignature(NetflixError):
    pass

class MissingAccessTokenError(NetflixError):
    pass

class TitleAlreadyInQueue(NetflixError):
    pass

class NetflixObject(object):
    def get(self, netflix=None, token=None, key=None, secret=None):
        netflix = netflix or getattr(self, 'netflix', None) or Netflix(key=key, secret=secret)
        return netflix.request(self, token=token)

class NetflixLink(NetflixObject, unicode):

    def __new__(self, href, *a, **kw):
        return unicode.__new__(self, href)

    def __init__(self, href=None, rel=None, title=None):
        self.href, self.rel, self.title = href, rel, title

    def __repr__(self):
        return "<%s %s>" % (type(self).__name__, self.href)

class NetflixCategory(NetflixObject, unicode):

    def __new__(self, label=None, scheme=None, term=None, content=None):
        return unicode.__new__(self, term)

    def __init__(self, label=None, scheme=None, term=None, content=None):
        self.label, self.scheme, self.term, self.content = label, scheme, term, content

    def __repr__(self):
        return "<%s %s>" % (type(self).__name__, self)

    def __unicode__(self):
        return self.term

class NetflixAvailability(NetflixCategory):

    def __new__(self, d):
        return unicode.__new__(self, d['category']['term'])

    def __init__(self, d):
        cat = d['category']

        super(NetflixAvailability, self).__init__(**cat)
        try:
            self.available_from = datetime.fromtimestamp(float(d['available_from']))
            self.available = False
        except KeyError:
            self.available_from = None
        try:
            self.available_until = datetime.fromtimestamp(float(d['available_until']))
        except KeyError:
            self.available_until = None

    def __repr__(self):
        return "<%s %s>" % (type(self).__name__, self)

class FancyObject(NetflixObject):
    def __init__(self, d):
        self.links = dict((di['title'], NetflixLink(**di)) for di in d.pop('link'))
        for k in d:
            setattr(self, k, d[k])
        super(FancyObject, self).__init__()

class CatalogTitle(FancyObject):

#     def __new__(self, d):
#         return str.__new__(d['id'])

    def __init__(self, d):
        title = d.pop('title')
        self.title = title['regular']
        self.title_short = title['short']
        categories = d.pop('category')
        self.categories = [NetflixCategory(**di) for di in categories]
        super(CatalogTitle, self).__init__(d)


    def __repr__(self):
        return "<%s %s %s>" % (type(self).__name__, self.title, self.id)

    def __unicode__(self):
        return self.title

    def __str__(self):
        return self.title

#     def __getattr__(self, name):
#         return getattr(self.id, name)

#     def __getitem__(self, key):
#         return self.id[key]

    def __eq__(self, other):
        return self.id == other.id

class NetflixUser(FancyObject):

    def __init__(self, d):
        preferred_formats = d.pop('preferred_formats')
        if not isinstance(preferred_formats, (list, tuple)):
            preferred_formats = [preferred_formats]
        self.preferred_formats = [NetflixCategory(**dd['category']) for dd in preferred_formats]
        super(NetflixUser, self).__init__(d)

    def __repr__(self):
        return "<%s %s %s>" % (type(self).__name__, self.last_name, self.user_id)

    def __unicode__(self):
        return "%s %s" % (self.first_name, self.last_name)

    def __str__(self):
        return unicode(self)

class NetflixCollection(FancyObject):
    item_type = CatalogTitle
    def __init__(self, d):
        try:
            items = d.pop(self._items_name)
        except AttributeError:
            raise NotImplemened("NetflixCollection subclasses must set _items_name")
        except KeyError:
            self.items = []
        else:
            if not isinstance(items, (list, tuple)):
                items = [items]
            self.items = [self.item_type(dd) for dd in items]
        super(NetflixCollection, self).__init__(d)
        for lab in 'number_of_results', 'results_per_page', 'start_index':
            setattr(self, lab, int(getattr(self, lab)))

    def __contains__(self, item):
        return item in self.items

    def __iter__(self):
        for item in self.items:
            yield item


class RentalHistory(NetflixCollection):
    _items_name = "rental_history_item"

class NetflixQueue(NetflixCollection):
    _items_name = 'queue_item'

    def __contains__(self, item):
        if isinstance(item, self.item_type):
            return super(NetflixQueue, self).__contains__(item)
        elif isinstance(item, basestring):
            return item in [i.links[i.title].href for i in self]
        try:
            return item.netflix_id in self
        except AttributeError:
            pass
        return False

class Netflix(object):
    protocol = "http://"
    host = 'api.netflix.com'
    port = '80'
    request_token_url = 'http://api.netflix.com/oauth/request_token'
    access_token_url  = 'http://api.netflix.com/oauth/access_token'
    authorization_url = 'https://api-user.netflix.com/oauth/login'
    signature_method = oauth.OAuthSignatureMethod_HMAC_SHA1()
    http = urllib3.HTTPConnectionPool(host)

    def __init__(self, key, secret, application_name=None):
        self.consumer = oauth.OAuthConsumer(key, secret)
        self.application_name = application_name

    def object_hook(self, d):
        d = dict((str(k), v) for k, v in d.iteritems())

        def isa(label):
            return label in d and len(d) == 1

        if 'catalog_titles' in d:
            try:
                catalog_titles = d['catalog_titles']['catalog_title']
                if not isinstance(catalog_titles, list):
                    catalog_titles = [catalog_titles]
                return [CatalogTitle(di) for di in catalog_titles]
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
        elif isa('queue'):
            return NetflixQueue(d['queue'])
        else:
            return d

    def get_request_token(self):
        oa_req = OAuthRequest.from_consumer_and_token(
            self.consumer,
            http_url=self.request_token_url)
        oa_req.sign_request(self.signature_method,
                                  self.consumer,
                                  None)
        res = self.http.get_url(self.request_token_url, headers = oa_req.to_header())
        return  OAuthToken.from_string(res.data)

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
        req = self.http.get_url(oa_req.to_url())
        res = req.data
        logging.debug(res)
        id = cgi.parse_qs(res)['user_id'][0]

        return id, OAuthToken.from_string(res)

    def analyze_error(self, exc):
        error = exc.data
        try:
            error = json.loads(error)
            code = int(error['status']['status_code'])
            message = error['status']['message']
        except (KeyError, ValueError):
            code = exc.status
            message = error
        if code == 401:
            if message == "Access Token Validation Failed":
                raise AuthError(message)
            elif message == 'Invalid Signature':
                raise InvalidSignature(message)
        elif code == 404:
            raise NotFound(message)
        elif code == 400 and message == 'Missing Required Access Token':
            raise MissingAccessTokenError(message)
        elif code == 412 and message == 'Title is already in queue':
            raise TitleAlreadyInQueue()


        raise NetflixError(code, message)

    @call_interval(0.2)
    def request(self, url, token=None, verb='GET', **args):
        """`url` may be relative with regard to Netflix. Verb is a
        HTTP verb.

        """
        if isinstance(url, NetflixObject) and not isinstance(url, basestring):
            url = url.id
        if not url.startswith('http://'):
            url = self.protocol + self.host + url
        args['output'] = 'json'
        args['method'] = verb.upper()

        oa_req = OAuthRequest.from_consumer_and_token(self.consumer,
                                                      http_url=url,
                                                      parameters=args,
                                                      token=token)
        oa_req.sign_request(self.signature_method,
                            self.consumer,
                            token)

        req = self.http.urlopen('GET', oa_req.to_url())
        if not str(req.status).startswith('2'):
            self.analyze_error(req)
        o = json.loads(req.data, object_hook=self.object_hook)
        return o
