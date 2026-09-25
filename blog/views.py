from django.shortcuts import render
from blog.models import Author, Category, Post


def post_details(request, gotslug):

    post = Post.objects.get(slug=gotslug)

    context = {

        'post': post,

    }

    return render(request, 'post.html', context)



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