from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Link(models.Model):
    title = models.CharField(max_length=255, verbose_name='Заголовок страницы')
    description = models.TextField(verbose_name='Краткое описание')
    url = models.URLField(verbose_name='Ссылка на страницу')
    image = models.URLField(verbose_name='Картинка', blank=True, null=True)
    collection = models.ForeignKey('Collection', on_delete=models.CASCADE, verbose_name='Коллекция', related_name='links', default=1)
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата и время создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата и время изменения')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='links')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):

        if not self.title:
            self.title = "not available"
        if not self.description:
            self.description = "not available"

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Ссылка'
        verbose_name_plural = 'Ссылки'


class Collection(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(blank=True, null=True, verbose_name='Краткое описание')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата и время создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата и время изменения')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collections')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Коллекция'
        verbose_name_plural = 'Коллекции'