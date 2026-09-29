from django.shortcuts import render
from blog.models import Author, Category, Post

def homepage(request):

    categories = Category.objects.all()[0:3]

    featured = Post.objects.filter(featured=True)

    latest = Post.objects.order_by('-timestamp')[0:3]

    context = {

        'featured': featured,

        'latest': latest,

        'categories': categories,

    }

    return render(request, 'homepage.html', context)

def about(request):

    return render(request, 'about_page.html')