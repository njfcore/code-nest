from django.shortcuts import render
from blog.models import Author, Category, Post

def homepage(request):

    categories = Category.objects.all()[0:3]

    featured = Post.objects.filter(featured=True)

    latest = Post.objects.order_by('-timestamp')[0:3]

    context = {

        'object_list': featured,

        'latest': latest,

        'categories': categories,

    }

    return render(request, 'homepage.html', context)

def post(request, gotslug):

    post = Post.objects.get(slug=gotslug)

    context = {

        'post': post,

    }

    return render(request, 'post.html', context)


def about(request):

    return render(request, 'about_page.html')

def category_post_list(request, gotslug):

    category = Category.objects.get(slug=gotslug)

    posts = Post.objects.filter(categories__in=[category])

    context = {

        'posts': posts,

    }

    return render(request, 'post_list.html', context)

def allposts(request):

    posts = Post.objects.order_by('-timestamp')

    context = {

        'posts': posts,

    }

    return render(request, 'all_posts.html', context)