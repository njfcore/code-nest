from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone

from subscription.services import can_access_post

from .models import Comment


def get_visible_comments(post):
    """
    Top-level comments with their live replies attached as
    `live_replies`. A deleted comment is kept only if it still
    has live replies under it.
    """
    replies = Comment.objects.select_related('user').order_by('created_at')

    comments = (
        Comment.objects
        .filter(post=post, parent__isnull=True)
        .select_related('user')
        .prefetch_related(Prefetch('replies', queryset=replies))
        .order_by('-created_at')
    )

    visible = []

    for comment in comments:
        comment.live_replies = [
            reply for reply in comment.replies.all()
            if not reply.is_deleted
        ]

        if comment.is_deleted and not comment.live_replies:
            continue

        visible.append(comment)

    return visible


def can_comment_on_post(user, post):
    return user.is_authenticated and can_access_post(user, post)


def add_comment(user, post, body, parent=None):
    if not can_comment_on_post(user, post):
        raise PermissionError(
            'You do not have access to comment on this post.'
        )

    body = body.strip()

    if not body:
        raise ValueError('Comment cannot be empty.')

    if parent is not None:
        if parent.post_id != post.id:
            raise ValueError('Invalid parent comment.')

        if parent.is_deleted:
            raise ValueError('You cannot reply to a deleted comment.')

        # Replies to a reply are attached to the top-level comment.
        if parent.parent_id is not None:
            parent = parent.parent

    return Comment.objects.create(
        post=post,
        user=user,
        parent=parent,
        body=body,
    )


def can_delete_comment(user, comment):
    if not user.is_authenticated:
        return False

    return comment.user_id == user.id or user.is_staff


@transaction.atomic
def delete_comment(user, comment):
    if not can_delete_comment(user, comment):
        raise PermissionError(
            'You cannot delete this comment.'
        )

    if comment.is_deleted:
        return comment

    comment.is_deleted = True
    comment.deleted_at = timezone.now()
    comment.body = ''
    comment.save(update_fields=['is_deleted', 'deleted_at', 'body'])

    return comment