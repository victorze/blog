from django.contrib.sitemaps import Sitemap

from .models import Post


class PostSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.9

    def items(self):
        # Por defecto, Django llama al método get_absolute_url() en cada objeto
        return Post.published.all()

    def lastmod(self, obj):
        # Recibe cada objeto devuelto por items() y devuelve la última vez que se modificó
        return obj.updated
