from django.db.models import Count
from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView
from taggit.models import Tag

from .models import Post, Comment
from .forms import EmailPostForm, CommentForm


class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'

def post_list(request, tag_slug=None):
    object_list = Post.published.all()
    tag = None

    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        object_list = object_list.filter(tags__in=[tag])

    paginator = Paginator(object_list, 2) # 2 post en cada página
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        # Si la página no es un entero, entregue la primera página
        posts = paginator.page(1)
    except EmptyPage:
        # Si la página está fuera de rango, entregue la última página
        posts = paginator.page(paginator.num_pages)
    return render(request, 'blog/post/list.html', {'page': page,
                                                   'posts': posts,
                                                   'tag': tag})

def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post, slug=post,
                                   status='published',
                                   publish__year=year,
                                   publish__month=month,
                                   publish__day=day)

    # Lista de comentarios activos para esta publicación
    comments = post.comments.filter(active=True)

    new_comment = None

    if request.method == 'POST':
        # Un comentario fue publicado
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            # Crear objeto de comentario pero aún no guardar en la base de datos
            new_comment = comment_form.save(commit=False)
            # Asignar la publicación actual al comentario
            new_comment.post = post
            # Guardar el comentario en la base de datos
            new_comment.save()
    else:
        comment_form = CommentForm()

    # Lista de publicaciones similares
    post_tags_ids = post.tags.values_list('id', flat=True) # [1, 2, 3, ...]
    similar_posts = Post.published.filter(tags__in=post_tags_ids)\
                                    .exclude(id=post.id)
    # Genera un campo calculado same_tags
    similar_posts = similar_posts.annotate(same_tags=Count('tags'))\
                                    .order_by('-same_tags', '-publish')[:4]

    return render(request,
           'blog/post/detail.html',
           {'post': post,
            'comments': comments,
            'new_comment': new_comment,
            'comment_form': comment_form,
            'similar_posts': similar_posts})


def post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id, status='published')
    sent = False

    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # Los campos del formulario pasaron la validación
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(
                post.get_absolute_url()
            )
            subject = f"{cd['name']} recommends you read " \
                      f"{post.title}"
            message = f"Read {post.title} at {post_url}\n\n" \
                      f"{cd['name']}\'s comments: {cd['comments']}"
            send_mail(subject, message, 'admin@gmail.com', [cd['to']])
            sent = True
    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html',
                  {'post': post, 'form': form, 'sent': sent})
