from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.contrib.auth.views import LoginView, LogoutView, \
     PasswordChangeView, PasswordResetView, PasswordResetDoneView, \
     PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import UpdateView, CreateView, \
                                      DeleteView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic.base import TemplateView
from django.views.decorators.cache import never_cache
from django.core.signing import BadSignature
from django.contrib.auth import logout
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages

from .models import AdvUser,  TestResult, UserStats, SubRubric, Bb, Comment
from .forms import ProfileEditForm, RegisterForm, SearchForm, \
     BbForm, AIFormSet, UserCommentForm, GuestCommentForm
from .utilities import signer

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import TestResult, UserStats
from django.db import models

from .wordlists import *

import random

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import TestResult, UserStats
from datetime import datetime, timedelta
import json

def index(request):
    bbs = Bb.objects.filter(is_active=True).select_related('rubric')[:10]
    context = {'bbs': bbs}
    return render(request, 'main/index.html', context)

def other_page(request, page):
    try:
        template = get_template('main/' + page + '.html')
    except TemplateDoesNotExist:
        raise Http404
    return HttpResponse(template.render(request=request))

class BBLoginView(LoginView):
    template_name = 'main/login.html'

# @login_required
# def profile(request):
#     bbs = Bb.objects.filter(author=request.user.pk)
#     context = {'bbs': bbs}
#     return render(request, 'main/profile.html', context)

class BBLogoutView(LogoutView):
    pass

class ProfileEditView(SuccessMessageMixin, LoginRequiredMixin, UpdateView):
    model = AdvUser
    template_name = 'main/profile_edit.html'
    form_class = ProfileEditForm
    success_url = reverse_lazy('main:profile')
    success_message = 'User data has been changed'

    def setup(self, request, *args, **kwargs):
        self.user_id = request.user.pk
        return super().setup(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, pk=self.user_id)

class PasswordEditView(SuccessMessageMixin, LoginRequiredMixin,
                                            PasswordChangeView):
    template_name = 'main/password_edit.html'
    success_url = reverse_lazy('main:profile')
    success_message = 'User password has successfully been changed'

class RegisterView(CreateView):
    model = AdvUser
    template_name = 'main/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('main:register_done')

class RegisterDoneView(TemplateView):
    template_name = 'main/register_done.html'

def user_activate(request, sign):
    try:
        username = signer.unsign(sign)
    except BadSignature:
        return render(request, 'main/activation_failed.html')
    user = get_object_or_404(AdvUser, username=username)
    if user.is_activated:
        template = 'main/activation_done_later.html'
    else:
        template = 'main/activation_done.html'
        user.is_active = True
        user.is_activated = True
        user.save()
    return render(request, template)

class ProfileDeleteView(SuccessMessageMixin, LoginRequiredMixin, DeleteView):
    model = AdvUser
    template_name = 'main/profile_delete.html'
    success_url = reverse_lazy('main:index')
    success_message = 'User has been successfully deleted'

    def setup(self, request, *args, **kwargs):
        self.user_id = request.user.pk
        return super().setup(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        logout(request)
        return super().post(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, pk=self.user_id)


class BBPasswordResetView(PasswordResetView):
    template_name = 'main/password_reset.html'
    subject_template_name = 'email/reset_letter_subject.txt'
    email_template_name = 'email/reset_letter_body.txt'
    success_url = reverse_lazy('main:password_reset_done')

class BBPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'main/password_reset_done.html'

class BBPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'main/password_reset_confirm.html'
    success_url = reverse_lazy('main:password_reset_complete')

class BBPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'main/password_reset_complete.html'


def typing_test(request):
    lang = request.GET.get('lang', 'en')
    word_pool = wordlists.get(lang, wordlists['en'])
    words = [random.choice(word_pool) for _ in range(400)]

    if request.method == 'POST' and request.user.is_authenticated:
        # Отримуємо результати з форми
        wpm = int(request.POST.get('wpm', 0))
        accuracy = float(request.POST.get('accuracy', 0))
        correct_words = int(request.POST.get('correct_words', 0))
        wrong_words = int(request.POST.get('wrong_words', 0))
        correct_chars = int(request.POST.get('correct_chars', 0))
        wrong_chars = int(request.POST.get('wrong_chars', 0))

        # Зберігаємо результат тесту
        TestResult.objects.create(
            user=request.user,
            wpm=wpm,
            accuracy=accuracy,
            correct_words=correct_words,
            wrong_words=wrong_words,
            correct_chars=correct_chars,
            wrong_chars=wrong_chars,
            language=lang
        )

        # Оновлюємо статистику користувача
        user_stats, created = UserStats.objects.get_or_create(user=request.user)
        user_stats.tests_completed += 1
        user_stats.total_chars += (correct_chars + wrong_chars)

        if wpm > user_stats.best_wpm:
            user_stats.best_wpm = wpm

        # Розраховуємо середній WPM
        all_results = TestResult.objects.filter(user=request.user)
        total_wpm = sum(result.wpm for result in all_results)
        user_stats.average_wpm = total_wpm / all_results.count()

        user_stats.save()

        messages.success(request, 'Ваш результат було збережено!')
        return redirect(request.get_full_path())

    # Отримуємо дані для таблиць лідерів
    top_tests = UserStats.objects.order_by('-tests_completed')[:20]
    top_wpm = UserStats.objects.order_by('-best_wpm')[:20]
    top_accuracy = TestResult.objects.values('user__username').annotate(
        avg_accuracy=models.Avg('accuracy')
    ).order_by('-avg_accuracy')[:20]

    context = {
        "words": words,
        "selected_lang": lang,
        "top_tests": top_tests,
        "top_wpm": top_wpm,
        "top_accuracy": top_accuracy,
    }

    return render(request, 'main/typing_test.html', context)


def typing_test_extended(request):
    lang = request.GET.get('lang', 'en')
    word_pool = wordlists_extended.get(lang, wordlists_extended['en'])
    words = [random.choice(word_pool) for _ in range(400)]

    if request.method == 'POST' and request.user.is_authenticated:
        # Отримуємо результати з форми
        wpm = int(request.POST.get('wpm', 0))
        accuracy = float(request.POST.get('accuracy', 0))
        correct_words = int(request.POST.get('correct_words', 0))
        wrong_words = int(request.POST.get('wrong_words', 0))
        correct_chars = int(request.POST.get('correct_chars', 0))
        wrong_chars = int(request.POST.get('wrong_chars', 0))

        # Зберігаємо результат тесту
        TestResult.objects.create(
            user=request.user,
            wpm=wpm,
            accuracy=accuracy,
            correct_words=correct_words,
            wrong_words=wrong_words,
            correct_chars=correct_chars,
            wrong_chars=wrong_chars,
            language=lang
        )

        # Оновлюємо статистику користувача
        user_stats, created = UserStats.objects.get_or_create(user=request.user)
        user_stats.tests_completed += 1
        user_stats.total_chars += (correct_chars + wrong_chars)

        if wpm > user_stats.best_wpm:
            user_stats.best_wpm = wpm

        # Розраховуємо середній WPM
        all_results = TestResult.objects.filter(user=request.user)
        total_wpm = sum(result.wpm for result in all_results)
        user_stats.average_wpm = total_wpm / all_results.count()

        user_stats.save()

        messages.success(request, 'Ваш результат було збережено!')
        return redirect(request.get_full_path())

    # Отримуємо дані для таблиць лідерів
    top_tests = UserStats.objects.order_by('-tests_completed')[:20]
    top_wpm = UserStats.objects.order_by('-best_wpm')[:20]
    top_accuracy = TestResult.objects.values('user__username').annotate(
        avg_accuracy=models.Avg('accuracy')
    ).order_by('-avg_accuracy')[:20]

    context = {
        "words": words,
        "selected_lang": lang,
        "top_tests": top_tests,
        "top_wpm": top_wpm,
        "top_accuracy": top_accuracy,
    }

    return render(request, 'main/typing_test.html', context)

def custom_test_settings(request):
    if request.method == "POST":
        randomize = "randomize" in request.POST
        duration = int(request.POST.get("duration", 60))
        custom_words = request.POST.get("custom_words", "")

        words = custom_words.strip().split()

        # Якщо слів мало, повторюємо їх до 400
        if len(words) < 400:
            words = (words * (400 // len(words) + 1))[:400]

        # Якщо вибрано рандомізацію, перемішуємо слова
        if randomize:
            random.shuffle(words)

        context = {
            "test_started": True,
            "words": words,
            "duration": duration,
            "randomize": randomize,
            "custom_words": custom_words,
        }
        return render(request, "main/about.html", context)

    return render(request, "main/about.html", {
        "test_started": False,
        "custom_words": "",
        "randomize": False,
    })


def multiplayer(request):
    # Вибираємо випадкові слова для гри
    lang = request.GET.get('lang', 'en')
    word_pool = wordlists.get(lang, wordlists['en'])
    words = [random.choice(word_pool) for _ in range(400)]
    text = ' '.join(words)

    context = {
        'text': text,
        'duration': 60,  # 1 хвилина за замовчуванням
        'username': request.user.username if request.user.is_authenticated else 'Guest_' + str(
            random.randint(1000, 9999)),
    }
    return render(request, 'main/multiplayer.html', context)


def learning_tests_view(request):
    # Здесь можно добавить логику проверки прогресса пользователя
    context = {
        'unlocked_levels': ['home-row', 'fj'],  # Пример разблокированных уровней
        'user_scores': {  # Пример результатов пользователя
            'home-row': 75,
            'fj': 55,
        }
    }
    return render(request, 'main/learning_tests.html', context)


def learning_test(request, test_id):
    # Словари с упражнениями для каждого теста

    words = learning_tests.get(test_id, learning_tests['home-row'])

    context = {
        'words': words,
        'test_id': test_id,
        'test_name': {
            'home-row': 'Домашній ряд',
            'df jk': 'Клавіші D та J',  # Додано
            'as l;': 'Клавіші A та L;',  # Додано
            'vb nm': 'Клавіші V та N',  # Додано
            'tg yh': 'Клавіші T та Y',  # Додано
            'er ui': 'Клавіші E та U',  # Додано
            'qw op': 'Клавіші Q та O',  # Додано
            'xc , .': 'Клавіші X, Кома та Точка',  # Додано
            'z ! ? /': 'Клавіші Z, Відкритий знак оклику, Знак питання та Коса риска',  # Додано
            'special symbols': 'Алфавітний тест',
            'CAPITAL letters': 'Тест великих літер',
            'Numbers 01-99': 'Числовий тест від 01 до 99',
            'All symbols': 'Тест всіх символів'
        }.get(test_id, 'Невідомий тест')
    }

    return render(request, 'main/learning_test_detail.html', context)

def custom_typing_test(request):
    words = request.session.get("custom_words", [])
    duration = request.session.get("custom_duration", 60)

    return render(request, "main/typing_test.html", {
        "words": words,
        "selected_lang": "custom",
        "duration": duration
    })

def bb_detail(request, rubric_pk, pk):
    bb = Bb.objects.get(pk=pk)
    initial = {'bb': bb.pk}
    if request.user.is_authenticated:
        initial['author'] = request.user.username
        form_class = UserCommentForm
    else:
        form_class = GuestCommentForm
    form = form_class(initial=initial)
    if request.method == 'POST':
        c_form = form_class(request.POST)
        if c_form.is_valid():
            c_form.save()
            messages.add_message(request, messages.SUCCESS,
                                 'Comment successfully added')
            return redirect(request.get_full_path_info())
        else:
            form = c_form
            messages.add_message(request, messages.WARNING,
                                 'Comment is not added')
    ais = bb.additionalimage_set.all()
    comments = Comment.objects.filter(bb=pk, is_active=True)
    context = {'bb': bb, 'ais': ais, 'comments': comments, 'form': form}
    return render(request, 'main/bb_detail.html', context)


@login_required
def profile(request):
    # Отримуємо статистику користувача
    user_stats = UserStats.objects.get(user=request.user)

    # Отримуємо останні 10 результатів тестів для графіка
    test_results = TestResult.objects.filter(user=request.user).order_by('-test_date')[:10]

    # Готуємо дані для графіка
    chart_data = {
        'dates': [result.test_date.strftime('%Y-%m-%d') for result in test_results],
        'wpm': [result.wpm for result in test_results],
        'accuracy': [result.accuracy for result in test_results]
    }

    # Розраховуємо слова за останній тиждень
    week_ago = datetime.now() - timedelta(days=7)
    weekly_words = sum(
        result.correct_words + result.wrong_words
        for result in TestResult.objects.filter(
            user=request.user,
            test_date__gte=week_ago
        )
    )

    context = {
        'user_stats': user_stats,
        'weekly_words': weekly_words,
        'chart_data': json.dumps(chart_data),
        'last_login': request.user.last_login,
        'date_joined': request.user.date_joined,
    }

    return render(request, 'main/profile.html', context)


