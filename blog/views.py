from django.shortcuts import render, get_object_or_404
from blog.models import Author, Category, Post
from subscription.services import can_access_post


def post_details(request, slug):

    post = get_object_or_404(Post, slug=slug)

    has_access = can_access_post(request.user, post)

    context = {

        'post': post,
        'has_access': has_access,

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