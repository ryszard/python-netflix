python-netflix
==============

Simple client for the Netflix API. It allows you to query Netflix
RESTful resources basing on their url and provides handy Python
objects wrapping Netflix JSON. `python-netflix` also cares that you
don't exceed Netflix' 5 requests per second limit.

Example usage:

    >>> NETFLIX_API_KEY, NETFLIX_API_SECRET, NETFLIX_APPLICATION_NAME = your_credentials

    >>> flix = Netflix(key=NETFLIX_API_KEY,
                       secret=NETFLIX_API_SECRET,
                       application_name=NETFLIX_APPLICATION_NAME)

    >>> sopranos = flix.request('/catalog/titles/', term="The Sopranos", max_results=3)

    >>> sopranos
    [<CatalogTitle The Sopranos: Season 1 http://api.netflix.com/catalog/titles/series/60030356/seasons/60030356>,
     <CatalogTitle The Sopranos: Season 6: Part 2 http://api.netflix.com/catalog/titles/series/60030356/seasons/70058397>,
     <CatalogTitle The Sopranos: Season 6: Part 1 http://api.netflix.com/catalog/titles/series/60030356/seasons/70020010>]


    >>> season1 = sopranos[0]

    >>> season1.average_rating
    4.4000000000000004

    >>> season1.categories
    [<NetflixCategory TV-MA>,
     <NetflixCategory Television>,
     <NetflixCategory TV Dramas>,
     <NetflixCategory TV Crime Dramas>,
     <NetflixCategory Must-See TV Dramas>,
     <NetflixCategory HBO>,
     <NetflixCategory Blu-ray>]

    >>> season1.title
    u'The Sopranos: Season 1'

    >>> season1.links
    {u'The Sopranos': <NetflixLink http://api.netflix.com/catalog/titles/series/60030356>,
     u'cast': <NetflixLink http://api.netflix.com/catalog/titles/series/60030356/seasons/60030356/cast>,
     u'directors': <NetflixLink http://api.netflix.com/catalog/titles/series/60030356/seasons/60030356/directors>,
     u'discs': <NetflixLink http://api.netflix.com/catalog/titles/series/60030356/seasons/60030356/discs>,
     u'formats': <NetflixLink http://api.netflix.com/catalog/titles/series/60030356/seasons/60030356/format_availability>,
     u'languages and audio': <NetflixLink http://api.netflix.com/catalog/titles/series/60030356/seasons/60030356/languages_and_audio>,
     u'official webpage': <NetflixLink http://www.hbo.com/sopranos/>,
     u'screen formats': <NetflixLink http://api.netflix.com/catalog/titles/series/60030356/seasons/60030356/screen_formats>,
     u'similars': <NetflixLink http://api.netflix.com/catalog/titles/series/60030356/seasons/60030356/similars>,
     u'synopsis': <NetflixLink http://api.netflix.com/catalog/titles/series/60030356/seasons/60030356/synopsis>,
     u'web page': <NetflixLink http://www.netflix.com/Movie/The_Sopranos_Season_1/60030356>}

    >>> discs = season1.links['discs'].get(flix)

    >>> discs
    [<CatalogTitle The Sopranos: Season 1: Disc 1 http://api.netflix.com/catalog/titles/discs/60003464>,
     <CatalogTitle The Sopranos: Season 1: Disc 2 http://api.netflix.com/catalog/titles/discs/60003465>,
     <CatalogTitle The Sopranos: Season 1: Disc 3 http://api.netflix.com/catalog/titles/discs/60003466>,
     <CatalogTitle The Sopranos: Season 1: Disc 4 http://api.netflix.com/catalog/titles/discs/60003467>]


`python-netflix` was written for [SetJam](http://setjam.com).

An alternative for python-netflix is
[pyflix](http://code.google.com/p/pyflix/) which uses a somewhat
different interface.
