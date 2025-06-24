from django.db import models
from django.contrib.auth.models import AbstractUser

from .utilities import get_timestamp_path

class AdvUser(AbstractUser):
    is_activated = models.BooleanField(default=True, db_index=True,
                                       verbose_name='User went through activation')
    send_messages = models.BooleanField(default=True,
                  verbose_name='Send user messages')

    def delete(self, *args, **kwargs):
        for bb in self.bb_set.all():
            bb.delete()
        super().delete(*args, **kwargs)

    class Meta(AbstractUser.Meta):
        pass

class TestResult(models.Model):
    user = models.ForeignKey(AdvUser, on_delete=models.CASCADE)
    wpm = models.PositiveIntegerField(verbose_name='Слів за хвилину')
    accuracy = models.FloatField(verbose_name='Точність')
    correct_words = models.PositiveIntegerField(verbose_name='Правильні слова')
    wrong_words = models.PositiveIntegerField(verbose_name='Неправильні слова')
    correct_chars = models.PositiveIntegerField(verbose_name='Правильні символи')
    wrong_chars = models.PositiveIntegerField(verbose_name='Неправильні символи')
    test_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата тесту')
    language = models.CharField(max_length=2, verbose_name='Мова', default='en')

    class Meta:
        verbose_name = 'Результат тесту'
        verbose_name_plural = 'Результати тестів'
        ordering = ['-wpm']

    def __str__(self):
        return f"{self.user.username} - {self.wpm} WPM ({self.test_date})"

class UserStats(models.Model):
    user = models.OneToOneField(AdvUser, on_delete=models.CASCADE)
    tests_completed = models.PositiveIntegerField(default=0, verbose_name='Пройдено тестів')
    best_wpm = models.PositiveIntegerField(default=0, verbose_name='Найкращий WPM')
    average_wpm = models.FloatField(default=0, verbose_name='Середній WPM')
    total_chars = models.PositiveIntegerField(default=0, verbose_name='Всього символів')

    class Meta:
        verbose_name = 'Статистика користувача'
        verbose_name_plural = 'Статистики користувачів'

    def __str__(self):
        return f"Статистика {self.user.username}"

class Rubric(models.Model):
    name = models.CharField(max_length=20, unique=True,
                            verbose_name='Name')
    order = models.SmallIntegerField(default=0, db_index=True,
                                     verbose_name='Order')
    super_rubric = models.ForeignKey('SuperRubric',
                   on_delete=models.PROTECT, null=True, blank=True,
                   verbose_name='SuperRubric')

class SuperRubricManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(super_rubric__isnull=True)

class SuperRubric(Rubric):
    objects = SuperRubricManager()
    def __str__(self):
        return self.name

    class Meta:
        proxy = True
        ordering = ('order', 'name')
        verbose_name = 'SuperRubric'
        verbose_name_plural = 'SuperRubrics'

class SubRubricManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(super_rubric__isnull=False)

class SubRubric(Rubric):
    objects = SubRubricManager()
    def __str__(self):
        return '%s - %s' % (self.super_rubric.name, self.name)

    class Meta:
        proxy = True
        ordering = ('super_rubric__order', 'super_rubric__name', 'order',
                    'name')
        verbose_name = 'SubRubric'
        verbose_name_plural = 'SubRubrics'

class Bb(models.Model):
    rubric = models.ForeignKey(SubRubric, on_delete=models.PROTECT,
                                          verbose_name='Rubric')
    title = models.CharField(max_length=40, verbose_name='Goods')
    content = models.TextField(verbose_name='Content')
    price = models.FloatField(default=0, verbose_name='Price')
    contacts = models.TextField(verbose_name='Contacts')
    image = models.ImageField(blank=True, upload_to=get_timestamp_path,
                              verbose_name='Image')
    author = models.ForeignKey(AdvUser, on_delete=models.CASCADE,
                               verbose_name='Author')
    is_active = models.BooleanField(default=True, db_index=True,
                                    verbose_name='Show in list')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True,
                                      verbose_name='Published')

    def delete(self, *args, **kwargs):
        for ai in self.additionalimage_set.all():
            ai.delete()
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name_plural = 'Goods'
        verbose_name = 'Goods'
        ordering = ['-created_at']

class AdditionalImage(models.Model):
    bb = models.ForeignKey(Bb, on_delete=models.CASCADE,
                           verbose_name='Goods')
    image = models.ImageField(upload_to=get_timestamp_path,
                              verbose_name='Image')

    class Meta:
        verbose_name_plural = 'Additional image'
        verbose_name = 'Additional images'

class Comment(models.Model):
    bb = models.ForeignKey(Bb, on_delete=models.CASCADE,
                               verbose_name='Goods')
    author = models.CharField(max_length=30, verbose_name='Author')
    content = models.TextField(verbose_name='Content')
    is_active = models.BooleanField(default=True, db_index=True,
                                    verbose_name='Show in list')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True,
                                      verbose_name='Published')

    class Meta:
        verbose_name_plural = 'Comments'
        verbose_name = 'Comments'
        ordering = ['created_at']
