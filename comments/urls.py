from django.urls import path

from . import views

app_name = 'comments'

urlpatterns = [
    path('post/<slug:slug>/', views.comment_list, name='list'),
    path('<int:comment_id>/reply/', views.reply, name='reply'),
    path('<int:comment_id>/delete/', views.delete, name='delete'),
]