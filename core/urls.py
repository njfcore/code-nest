from django.urls import path, include

from .views import *

urlpatterns = [
    path("", homepage, name="home"),
    path("about/", about, name="about"),
]