from django.conf.urls import patterns, url, include


from usda import views

urlpatterns = patterns('',
	#url(r"^(\d+)/$", views.show_food, name="show" ),
	url(r"^food/(?P<pk>\d+)/$", views.FoodDetail.as_view(), name="show_food" ),
	url(r"^$", views.main, name="main"),
)
