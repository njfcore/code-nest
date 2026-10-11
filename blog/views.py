from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
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

    paginator = Paginator(
        posts,
        9,
    )

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(
        page_number,
    )

    context = {

        'page_obj': page_obj,
        'category': category,
        'total_posts': paginator.count,

    }

    return render(request, 'post_list.html', context)

def allposts(request):

    posts = Post.objects.all().order_by('-timestamp')

    paginator = Paginator(
        posts,
        9,
    )
    
    page_number = request.GET.get("page")
    
    page_obj = paginator.get_page(
        page_number,
    )

    context = {

        'page_obj': page_obj,
        'total_posts': paginator.count,

    }

    return render(request, 'all_posts.html', context)

def categories_view(request):

    categories = Category.objects.all()

    paginator = Paginator(
        categories,
        9,
    )
        
    page_number = request.GET.get("page")
        
    page_obj = paginator.get_page(
        page_number,
    )

    context = {

        'page_obj': page_obj,
        'total_categories': paginator.count,

    }

    return render(request, 'categories_page.html', context)