from django.conf import settings

from django.contrib import admin

from .views import post_details, category_post_list, allposts, categories_view 

from django.urls import path

app_name = "blog"

urlpatterns = [

    path('categories/', categories_view, name="categories"),

    path('post/<slug:slug>/', post_details, name='postdetails'),

    path('posts/', allposts, name='allposts'),

    path('postlist/<slug:slug>/', category_post_list, name='postlist'),
    
]