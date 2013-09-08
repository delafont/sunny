from django.conf.urls import patterns, url

from graph import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^response.json/?$', views.json_response, name='json_response'),
    url(r'^newsample.json/?$', views.new_sample, name='new_sample'),
    url(r'^clear.json/?$', views.clear_all_db, name='clear_all_db'),
    #url(r'^createImages/?$', views.create_images, name='create_images'),
)

