from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from blog.models import Post
from subscription.services import can_access_post

from .forms import CommentForm
from .models import Comment
from .services import (
    add_comment,
    can_comment_on_post,
    can_delete_comment,
    delete_comment,
    get_visible_comments,
)

COMMENTS_PER_PAGE = 10


def _redirect_back(request, post, anchor=''):
    """
    Redirect to the page the user came from (the `next` hidden field),
    falling back to the first page of the post's comments.
    """
    next_url = request.POST.get('next', '')

    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        target = next_url.split('#')[0]
    else:
        target = reverse('comments:list', args=[post.slug])

    return redirect(f'{target}#{anchor}' if anchor else target)


def comment_list(request, slug):
    post = get_object_or_404(Post, slug=slug, is_published=True)

    # Pro posts: no access means no comments either.
    if not can_access_post(request.user, post):
        return redirect('blog:postdetails', slug=post.slug)

    form = CommentForm()

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())

        form = CommentForm(request.POST)

        if form.is_valid():
            try:
                comment = add_comment(
                    request.user,
                    post,
                    form.cleaned_data['body'],
                )
            except (PermissionError, ValueError) as error:
                messages.error(request, str(error))
            else:
                messages.success(request, 'Your comment was posted.')
                list_url = reverse('comments:list', args=[post.slug])
                return redirect(f'{list_url}#comment-{comment.id}')

    comments = get_visible_comments(post)

    total_comments = sum(
        (0 if comment.is_deleted else 1) + len(comment.live_replies)
        for comment in comments
    )

    page_obj = Paginator(comments, COMMENTS_PER_PAGE).get_page(
        request.GET.get('page')
    )

    for comment in page_obj:
        comment.can_delete = can_delete_comment(request.user, comment)

        for reply in comment.live_replies:
            reply.can_delete = can_delete_comment(request.user, reply)

    context = {
        'post': post,
        'form': form,
        'page_obj': page_obj,
        'total_comments': total_comments,
        'can_comment': can_comment_on_post(request.user, post),
    }

    return render(request, 'comments/comment_list.html', context)


@login_required
@require_POST
def reply(request, comment_id):
    parent = get_object_or_404(
        Comment.objects.select_related('post', 'parent'),
        id=comment_id,
        post__is_published=True,
    )
    post = parent.post

    form = CommentForm(request.POST)

    if not form.is_valid():
        error_text = form.errors.get('body', ['Invalid reply.'])[0]
        messages.error(request, error_text)
        return _redirect_back(request, post, f'comment-{parent.id}')

    try:
        new_reply = add_comment(
            request.user,
            post,
            form.cleaned_data['body'],
            parent=parent,
        )
    except (PermissionError, ValueError) as error:
        messages.error(request, str(error))
        return _redirect_back(request, post, f'comment-{parent.id}')

    messages.success(request, 'Your reply was posted.')
    return _redirect_back(request, post, f'comment-{new_reply.id}')


@login_required
@require_POST
def delete(request, comment_id):
    comment = get_object_or_404(
        Comment.objects.select_related('post'),
        id=comment_id,
    )

    try:
        delete_comment(request.user, comment)
    except PermissionError as error:
        messages.error(request, str(error))
    else:
        messages.success(request, 'Comment deleted.')

    return _redirect_back(request, comment.post)