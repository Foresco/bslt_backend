from django.contrib import admin
from .models import ExternalPartner, ExchangeSession, ExternalID

class ExternalIDAdmin(admin.ModelAdmin):
    list_display = ('internal', 'partner', 'external_id')
    list_filter = ['partner']
    search_fields = ['internal']
    ordering = ('internal', 'partner')


# Со специальными настройками
admin.site.register(ExternalID, ExternalIDAdmin)

# Без специальных настроек
admin.site.register(ExternalPartner)
admin.site.register(ExchangeSession)
