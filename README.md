Bulldog
=======

Bulldog is a Django middleware module to implement resource based
access control for your RESTful API. The access control can be
configured per resource for each of the four methods
(POST/GET/PUT/DELETE). This means that each user can have different
set of resources with different request methods available. More
detailed explanatin can be found from my [blog post][1].


Implementation
--------------

The implementation utilizes Django's built-in `user`, `group` and
`permission` model and thus permissions may be assigned using Django's
own admin-interfaces. Bulldog automatically populates the permission
table with all necessary permissions. Each protected resource will
generate four permissions (one for each request method). These
permissions can then be added to users and groups.


Requirements
------------

**Resources must have names**. Each protected resource needs to have
the `name` property defined in `urls.py`. For example:

      urlpatterns = patterns('',
        url(r'^order$', 'myapi.views.orders', name="orders"),
        url(r'^user$', 'myapi.views.users', name="vehicle"),
        )

**Requests must be authenticated**. An authentication middleware must
be configured to take care of the user authentication before the
request hits the bulldog layer. In Django terms this means that
`request.user` must be set.

Installation
------------

Make sure bulldog.py is in ´PYTHONPATH` and then add it to your
middlewares in settings.py. For example:

     MIDDLEWARE_CLASSES = (
       'django.middleware.gzip.GZipMiddleware',
       'django.middleware.common.CommonMiddleware',
       'mymiddleware.basicauth.BasicAuthentication',
       'mymiddleware.bulldog.Bulldog',
     )
     
Next, you need to tell bulldog which resources should be
protected. You can say by adding following parameters to your
settings.py:

     BULLDOG_URLS_MODULES = (
       'mysite.api.urls',
       )

     BULLDOG_URLS = (
       r'^/api',
       )


`BULLDOG_URLS_MODULES` defines the modules that have the url mappings
to your resources. Bulldog needs these to find all the `name`s of your
resources. **NOTE: if you forget to give a name for any of the URL
mappings, bulldog cannot enforce access control rules and allows
access.**

`BULLDOG_URLS` is optional parameter to provide a regexp to make sure
that all requests that satisfy the regexp are protected by bulldog
even if the url mapping doesn't have the `name` attribute.

Finally, make sure that you have authentication middleware configured
(as mentioned earlier) and applications `django.contrib.auth` and
`django.contrib.contenttypes` installed (remember to run `syncdb` if
you just added these apps).

[1]:http://wuher-random.blogspot.com/2011/09/access-control-for-your-restful-api.html
