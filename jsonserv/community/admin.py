from django.contrib import admin
from jsonserv.core.admin import ListAdmin

from jsonserv.community.models import LetterDirection, LetterType, TaskType

# Простые списки
admin.site.register(LetterDirection, ListAdmin)
admin.site.register(LetterType, ListAdmin)
admin.site.register(TaskType, ListAdmin)
