# -*- coding: utf-8 -*-

"""
Django middleware class to implement access control for RESTful APIs.

todo: detailed description

"""


import re
from django.http import HttpResponse
from django.core.urlresolvers import resolve
from django.utils.importlib import import_module


__author__ = 'Janne Kuuskeri (janne.kuuskeri@gmail.com)'
__copyright__ = 'Copyright 2011, Janne Kuuskeri'
__license__ = 'MIT'


class Bulldog(object):
    """ Access control for resources. """
    

    REQUEST_METHODS = ('post', 'get', 'put', 'delete',)
    PERM_APP_NAME = 'bulldog'
    SETTINGS_URLS = 'BULLDOG_URLS'
    SETTINGS_URLS_MODULES = 'BULLDOG_URLS_MODULES'


    def __init__(self):
        """
        Find all guarded resource based on settings and add missing
        permissions to database.
        """

        self._urlnames = self._get_all_url_names()
        self._guarded_urls = self._get_guarded_urls()
        self._update_db()
        
    def _is_guarded_resource(self, name, path):
        """
        Check whether the resource should be guarded by bulldog or not.

        Parameters:
        name -- url name (as specified in urls.py)
        path -- requested url
        """

        if name in self._urlnames:
            return True

        for urlpattern in self._guarded_urls:
            if re.match(urlpattern, path) != None:
                return True
        
    def _get_guarded_urls(self):
        """
        Find all guarded URL patterns as defined in settings module. These
        URLs are top level URLs to guard every resource beneath them.
        """

        import settings
        if hasattr(settings, self.SETTINGS_URLS):
            return getattr(settings, self.SETTINGS_URLS)
        else:
            return None

    def _get_permission_description(self, permission_name):
        """
        Convert a descriptive string based on the permission name.

        Fox example: 'resource_order_get'  ->  'Can GET order'
        """

        _, resource, method = permission_name.split('_')
        return 'Can %s %s' % (method.upper(), resource)

    def _get_permission_name(self, url_name, request_method):
        """
        Compose permission name from url name and request method. This
        name is used when checking permissions later.

        Parameters:
        url_name -- url name in lower case
        request_method -- request method in lower case
        """

        return 'resource_%s_%s' % (url_name, request_method)

    def _get_url_names(self, modname):
        """
        Get URL names of a single urls module.
        """

        urlmod = import_module(modname)
        return [url.__dict__['name'] for url in urlmod.urlpatterns if url.__dict__['name']]

    def _get_all_url_names(self):
        """
        Get all URL names guarded by bulldog.
        """

        import settings
        ret = []
        if hasattr(settings, self.SETTINGS_URLS_MODULES):
            for urlmod in getattr(settings, self.SETTINGS_URLS_MODULES):
                ret += self._get_url_names(urlmod)
        return ret

    def _update_db(self):
        """
        Add the content type and all permissions if they are missing.
        """

        self._add_content_type()
        self._populate_permissions()

    def _add_content_type(self):
        """
        Add the bulldog content type to the database if it's missing.
        """

        from django.contrib.contenttypes.models import ContentType
        try:
            row = ContentType.objects.get(app_label=self.PERM_APP_NAME)
        except ContentType.DoesNotExist:
            row = ContentType(name=self.PERM_APP_NAME, app_label=self.PERM_APP_NAME, model=self.PERM_APP_NAME)
            row.save()
        self._permission_content_type = row.id

    def _populate_permissions(self):
        """
        Add all missing permissions to the database.
        """

        from django.contrib.auth.models import Permission
        # read the whole auth_permission table into memory
        allperms = [perm.codename for perm in Permission.objects.all()]
        for urlname in self._urlnames:
            perms = [self._get_permission_name(urlname, rm) for rm in self.REQUEST_METHODS]
            for perm in perms:
                if perm not in allperms:
                    Permission(name=self._get_permission_description(perm),
                               content_type_id=self._permission_content_type,
                               codename=perm).save()

    def has_perm(self, user, permission):
    
        """
        Return True if the user (or any of user's groups) has the
        given permission.

        Parameters:
        user -- user object
        permission -- name of the permission
        """

        if user.is_superuser:
            return True
        if user.is_active:
            return ('%s.%s' % (self.PERM_APP_NAME, permission)) in user.get_all_permissions()
        return False

    def check_permission(self, user, path, method):
        """ Check whether the user have access to the resource.

        Parameters:
        user -- user object
        path -- requested path (pointing to the resource)
        method -- request method

        Returns None if the user has the access, otherwice HttpResponse(403).
        """

        resource_name = resolve(path).url_name.lower()
        if not self._is_guarded_resource(resource_name, path):
            return None
        if self.has_perm(user, self._get_permission_name(resource_name, method.lower())):
            return None
        elif user.is_anonymous():
            return HttpResponse("Unauthorized", status=401)
        else:
            return HttpResponse("Forbidden", status=403)

    def process_request(self, request):
        """ Check whether the request is permitted or not.

        The given request needs to have the 'user' attribute present.
        This method then checks whether the user may apply the given
        method (GET, POST, ...) on the requsted resource.
        """

        if not hasattr(request, 'user'):
            raise ImproperlyConfigured(
                "Bulldog middleware depends on an authentication middleware."
                " Edit your MIDDLEWARE_CLASSES setting to insert"
                " one of the authentication middlewares before Bulldog.")

        return self.check_permission(request.user, request.path, request.method)
