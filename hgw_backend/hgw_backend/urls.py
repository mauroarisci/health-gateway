# Copyright (c) 2017-2018 CRS4
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
# AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


from django.urls import path, include
from django.conf.urls.static import static
from django.contrib import admin

from hgw_backend import views, settings
from hgw_common.settings import VERSION_REGEX

admin.autodiscover()

urlpatterns = [
    path(r'', admin.site.urls),
    path(r'protocol/', include('hgw_common.urls')),
    path(r'oauth2/', include('oauth2_provider.urls')),
    path(r'{}/sources/'.format(VERSION_REGEX), views.Sources.as_view({'get': 'list'})),
    path(r'{}/sources/<str:source_id>/'.format(VERSION_REGEX), views.Sources.as_view({'get': 'retrieve'})),
    path(r'{}/profiles/'.format(VERSION_REGEX), views.Profiles.as_view({'get': 'list'})),
    path(r'{}/messages/'.format(VERSION_REGEX), views.Messages.as_view()),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
