from django.conf import settings

from django.contrib import admin

from .views import post_details, category_post_list, allposts 

from django.urls import path

app_name = "blog"

urlpatterns = [

    path('post/<slug:slug>/', post_details, name='post details'),

    path('posts/', allposts, name='allposts'),

    path('postlist/<slug:slug>/', category_post_list, name='category post list'),
    
]