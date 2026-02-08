# import debug_toolbar  # Отладочный функционал Django
from django.contrib import admin
from django.apps import apps
from django.urls import path
from django.contrib.auth.decorators import login_required
from rest_framework.routers import SimpleRouter

import importlib

from jsonserv.core.views import ListView, DetailView

admin.site.site_header = 'Платформа Базальта'  # Заголовок админки
admin.site.enable_nav_sidebar = False  # Убираем панель слева в админке

router = SimpleRouter()

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('rest/', include('jsonserv.rest.urls')),  # REST-сервисы. Теперь они подключаются на общих основаниях
    # path('__debug__/', include(debug_toolbar.urls)),  # Обращение к отладочному функционалу
]

# Загрузка адресов из всех подключенных приложений
for app in apps.get_app_configs():
    # Каждое приложение должно иметь файл urls.py
    if app.name.startswith('jsonserv.'):
        # print(app.name + '.urls')
        urls = importlib.import_module(app.name + '.urls')
        if hasattr(urls, 'urlpatterns'):
            # print(app.name)
            # print(urls.urlpatterns)
            urlpatterns += urls.urlpatterns
        if hasattr(urls, 'router_urls'):
            for key in urls.router_urls:
                router.register(key, urls.router_urls[key])

# Регистрируем собранные паттерны
urlpatterns += router.urls

# Списки и формы свойств основных сущностей
# Добавляем в конце чтобы не перекрыть точные шаблоны
urlpatterns += [
    path('<int:id>/', login_required(DetailView.as_view()), name="exemplar"),
    path('<slug:type_key>/', login_required(ListView.as_view()), name="object_list"),
    path('<slug:type_key>/<int:id>/', login_required(DetailView.as_view()), name="sub_exemplar"),
    path('<slug:type_key>/<slug:sub_type_key>/', login_required(ListView.as_view()),  name="sub_object_list"),
]
