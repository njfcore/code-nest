from django.contrib import admin

from .models import Author, Category, Post

class CategoryAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "subtitle",
        "slug",
    )

    search_fields = (
        "title",
    )
class PostAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "slug",
        "overview",
        "author",
        "thumbnail",
        "is_pro",
        "is_published",
        "published_at",
    )  

    list_filter = (
        "is_published",
        "is_pro",
        "categories"
    ) 

    search_fields = (
        "title",
        "content",
        "author"
    )
     

admin.site.register(Author)

admin.site.register(Category, CategoryAdmin)

admin.site.register(Post, PostAdmin)