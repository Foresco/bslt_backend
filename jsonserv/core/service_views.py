# Служебные дашборды
from django.conf import settings  # для обращения к настройкам
from django.views.generic import FormView, RedirectView
from django.contrib import messages
from django.contrib.auth import logout, update_session_auth_hash
from django.shortcuts import render, redirect

from django.http import HttpResponseRedirect
from collections import OrderedDict
from ipware import get_client_ip  # Получение ip-пользователя
from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login, logout as auth_logout
from django.contrib.auth.hashers import check_password

from jsonserv.core import forms  # Формы собственной разработки
from jsonserv.core.models import UserProfile


class LoginView(FormView):
    """Класс для работы с формой входа"""
    template_name = 'login.html'  # Шаблон формы входа
    # Указание ссылок на собственные формы
    forms = {'user': forms.CustomAuthenticationForm,  # Форма аутентификации пользователя
             'session': forms.UserSessionFrom}  # Форма с данными о сессии пользователя
    redirect_field_name = REDIRECT_FIELD_NAME  # Название поля в параметрах, куда переходим после входа

    def get_context_data(self, **kwargs):
        context = super(LoginView, self).get_context_data(**kwargs)
        # Формирование приветствия на основе настроек
        enterprise = getattr(settings, 'ENTERPRISE', '')
        if enterprise:
            context['caption'] = f'Вход в информационную систему {enterprise}'
        else:
            context['caption'] = 'Вход в систему Базальта'
        return context

    def post(self, request, *args, **kwargs):
        # Обработка нажатия кнопки Войти
        form = self.get_form()  # Получаем описание форм
        # Проверяем правильность переданных данных для каждой из используемых форм
        # Именно в этот момент происходит аутентификация пользователя
        if form['user'].is_valid() and form['session'].is_valid():
            return self.form_valid(form)
        else:
            # Сюда идут при неудачной аутентификации
            return self.form_invalid(form)

    def get_form(self):
        # Геттер форм (требуется базовому функционалу)
        # В данном случае возвращает формы в виде отсортированного словаря
        user_form = self.forms['user'](**self.get_form_kwargs())
        session_from = self.forms['session'](**self.get_form_kwargs())
        form = OrderedDict([('user', user_form),
                            ('session', session_from)])
        return form

    def form_valid(self, form):
        # Обработка входа пользователя
        # Наполнение и сохранение модели транзакции
        session_model = form['session'].save(commit=False)
        session_model.user_ip, is_routable = get_client_ip(self.request)  # is_routable не используем (что это?)
        session_model.user = form['user'].get_user()
        # Сохранение модели транзакции
        session_model.save()
        # Добавление в параметры django-сессии идентификатора транзакции
        self.request.session['user_session_id'] = session_model.id
        # Проверка срока действия пароля # Добавление в параметры django-сессии требование смены пароля
        if getattr(session_model.user, 'userprofile', None):  # Если у пользователя есть профиль
            # Проверяем, не отмечен ли профиль, как не имеющий права входить
            if not session_model.user.userprofile.loginable():
                logout(self.request)
                return HttpResponseRedirect('/password')
                # return HttpResponseRedirect(self.g)
            # Проверка, не истек ли у пользователя срок действия пароля
            self.request.session['force_change_password'] = session_model.user.userprofile.is_password_date_expired()
        else:
            self.request.session['force_change_password'] = False

        auth_login(self.request, form['user'].get_user())  # Вызов типового метода аутентификации

        if self.request.session['force_change_password']:
            # Отправляем на форму изменения пароля
            return HttpResponseRedirect('/password')
        
        # Перенаправление на следующую страницу
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        # Получаем дашборд по умолчанию для пользователя
        default_url = UserProfile.get_user_dashboard(self.request.user)
        # Получаем переданный в запросе параметр next или next по умолчанию
        success_url = self.request.GET.get(self.redirect_field_name, default_url)
        return success_url


class LogoutView(RedirectView):
    def get(self, request, *args, **kwargs):
        self.url = request.GET.get('next', '/login/')
        auth_logout(request)  # Вызов типового метода стандартного фукнционала
        return super(LogoutView, self).get(request, *args, **kwargs)


# Простые представления
# Функционал смены пароля пользователем
def change_password(request):
    if request.method == 'POST':
        form = forms.CustomPasswordChangeForm(request.user, request.POST)
        # Проверяем, что пароль действительно изменился
        if check_password(form['new_password1'].value(), request.user.password):
            # messages.error(request, 'Пароль должен быть изменен!')
            return render(request, 'change_password.html', {
                'form': form,
                'caption': 'Требуется обязательная смена пароля' if request.session['force_change_password'] else 'Смена пароля пользователя',
                'non_field_errors': 'Пароль должен быть изменен!'
            })
        else:
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)
                if request.user.userprofile: # Если у пользователя есть профиль
                    # Запись факта изменения пароля
                    request.user.userprofile.set_password_changed(request.session['user_session_id']) 
                    # Убираем требование смены пароля
                    request.session['force_change_password'] = False
                # messages.success(request, 'Ваш пароль успешно изменен!')
                return redirect('search')
            else:
                messages.error(request, 'Пожалуйста, исправьте указанные замечания.')
    else:
        form = forms.CustomPasswordChangeForm(request.user)
    return render(request, 'change_password.html', {
        'form': form,
        'caption': 'Требуется обязательная смена пароля' if request.session['force_change_password'] else 'Смена пароля пользователя'
    })
