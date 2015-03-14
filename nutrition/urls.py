from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns('',
    # Examples:
    # url(r'^blog/', include('blog.urls')),

	url(r'^$', include('usda.urls',namespace="home")),
	url(r'^usda/', include('usda.urls',namespace="usda")),
    url(r'^admin/', include(admin.site.urls)),
)
