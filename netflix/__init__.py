
from oauth import oauth
import urllib2
from urllib import urlencode
try:
    import json
except ImportError:
    import simplejson as json

class NetflixObject(object):
    def get(self, netflix=None, key=None, secret=None):
        if not netflix:
            netflix = Netflix(key=key, secret=secret)
        return netflix.request(self)

class Printable(object):
    def __str__(self):
        return self._imp

    @property
    def _imp(self):
        return getattr(self, self.important)

    def __repr__(self):
        return "<%s %r>" % (type(self).__name__, self._imp)

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

class CatalogTitle(NetflixObject, Printable):
    important = 'title'
    def __init__(self, d):
        categories = d.pop('category')
        links = d.pop('link')
        title = d.pop('title')
        self.title = title['regular']
        self.title_short = title['short']
        for k in d:
            setattr(self, k, d[k])

        self.categories = [NetflixCategory(**di) for di in categories]
        self.links = dict((di['title'], NetflixLink(**di)) for di in links)

class Netflix(object):
    protocol = "http://"
    host = 'api.netflix.com'
    port = '80'
    request_token_url = 'http://api.netflix.com/oauth/request_token'
    access_token_url  = 'http://api.netflix.com/oauth/access_token'
    authorization_url = 'https://api-user.netflix.com/oauth/login'

    def __init__(self, key, secret):
        self.consumer = oauth.OAuthConsumer(key, secret)

    def object_hook(self, d):
        d = dict((str(k), v) for k, v in d.iteritems())
        if 'catalog_titles' in d:
            return [CatalogTitle(di) for di in d['catalog_titles']['catalog_title']]
        elif 'synopsis' in d and len(d) == 1:
            return d['synopsis']
        else:
            return d

    def get_request_token(self):
        oa_req = oauth.OAuthRequest.from_consumer_and_token(self.consumer,
                                                            http_url=self.request_token_url)
        oa_req.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(),
                                  self.consumer,
                                  None)
        req = urllib2.Request(self.request_token_url, headers = oa_req.to_header())
        request_token = oauth.OAuthToken.from_string(urllib2.urlopen(req).read())
        return request_token

    def request(self, url, **args):
        """`url` may be realtive with regard to Netflix.

        """
        if not url.startswith('http://'):
            url = self.protocol + self.host + url
        token = None
        args['output'] = 'json'
        oa_req = oauth.OAuthRequest.from_consumer_and_token(self.consumer,
                                                            http_url=url,
                                                            parameters=args,
                                                            token=token)
        oa_req.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(),
                            self.consumer,
                            token)

        req = urllib2.urlopen(oa_req.to_url())
        return json.load(req, object_hook=self.object_hook)

if __name__=="__main__":
    import pprint
    pp = pprint.PrettyPrinter(indent=2)
    def p(*a, **k):
        pp.pprint(*a, **k)

    n = Netflix(key='dydmw8gpezjh5kgfqw7afxnw', secret='kAP65KD7Zs')

    def r(*a, **kw):
        p(n.request(*a, **kw))

    n = Netflix(key='dydmw8gpezjh5kgfqw7afxnw', secret='kAP65KD7Zs')
    #print n.get_request_token()
    #n.request('http://api.netflix.com/catalog/titles/movies/60021896')
    #r = n.request('http://api.netflix.com/catalog/titles', term="The Sopranos")['catalog_titles']['catalog_title']
    #n.request('http://api.netflix.com/catalog/titles/series', term="The Sopranos")
    #pp.pprint(r[0])
    #q = n.request("http://api.netflix.com/catalog/titles/series/60030356")
    #f = CatalogTitle(q['catalog_title'])
    #print f
    #p(f.links)
    #p(f.categories)
    #p(n.request('http://api.netflix.com/catalog/titles', term="The Sopranos"))
    #p(n.request('http://api.netflix.com/catalog/titles/series/60030356/seasons/70058397/synopsis'))
    #r = n.request(u'/catalog/titles/series/60030356/seasons')
    #p(n.request('http://api.netflix.com/catalog/titles', term="Denial, Anger, Acceptance"))
    for o in (n.request('/catalog/titles', term="The Sopranos: Season 2")[0].links['discs'].get(n)):
        p(o.box_art)
        print

   # p(n.request('/catalog/titles', term="The Sopranos"))
    #p(r[0])
    #p(q)
    #pp.pprint(n.request(u'http://api.netflix.com/catalog/titles/series/60030356/seasons'))
    #p(n.request(u'http://api.netflix.com/catalog/titles/series/60030356/seasons/60030411'))
    #p(n.request(u'http://api.netflix.com/catalog/titles/series/60030356/seasons/60030411/discs'))
    #p(n.request(u'http://api.netflix.com/catalog/titles/discs/60021344/synopsis'))
    #p(n.request(u'http://api.netflix.com/catalog/titles//series/60030356/synopsis'))
    #r = n.request(u'http://api.netflix.com/catalog/titles/series/60030356/seasons/70058397/discs')
    #pp.pprint(r)
