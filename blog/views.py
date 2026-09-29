from django.shortcuts import render
from blog.models import Author, Category, Post


def post_details(request, slug):

    post = Post.objects.get(slug=slug)

    context = {

        'post': post,

    }

    return render(request, 'post.html', context)



def category_post_list(request, slug):

    category = Category.objects.get(slug=slug)

    posts = Post.objects.filter(categories__in=[category])

    context = {
        
        'category': category,
        'posts': posts,

    }

    return render(request, 'post_list.html', context)

def allposts(request):

    posts = Post.objects.all().order_by('-timestamp')

    context = {

        'posts': posts,

    }

    return render(request, 'all_posts.html', context)

def categories_view(request):

    categories = Category.objects.all()

    context = {

        'categories': categories
    }

    return render(request, 'categories_page.html', context)