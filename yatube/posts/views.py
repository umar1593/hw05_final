from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, get_user_model
from .utils import get_page_obj

User = get_user_model()


def index(request):
    post_list = Post.objects.all()
    page_obj = get_page_obj(post_list, request.GET.get('page'))
    context = {'page_obj': page_obj, 'index': True}
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = get_page_obj(posts, request.GET.get('page'))

    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    count = posts.count()
    page_number = request.GET.get('page')
    page_obj = get_page_obj(posts, page_number)
    user = request.user
    following = False
    if request.user.is_authenticated:
        following = user.follower.filter(author=author).exists()
    context = {
        'count': count,
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    form = CommentForm()
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    context = {
        'post': post,
        'form': form,
        'comments': comments,
        'post_id': post_id,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        form.instance.author = request.user
        form.save()
        return redirect('posts:profile', request.user)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user.id != post.author.pk:
        return redirect('posts:post_detail', post.pk)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )
    if form.is_valid():
        post = form.save()
        return redirect('posts:post_detail', post.pk)
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post.pk)


@login_required
def follow_index(request):
    fav_posts = Post.objects.filter(author__following__user=request.user)
    page_obj = get_page_obj(fav_posts, request.GET.get('page'))
    context = {'page_obj': page_obj, 'follow': True}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    following = Follow.objects.filter(user=user, author=author)
    if request.user != author and not following.exists():
        Follow.objects.create(user=request.user, author=author)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    following = user.follower.filter(author=author)
    following.delete()
    return redirect('posts:follow_index')
