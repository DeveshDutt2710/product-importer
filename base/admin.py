from django.contrib import admin


class BaseAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'created_at', 'updated_at', 'state')
    list_filter = ('state', 'created_at', 'updated_at')
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    search_fields = ('uuid',)
    ordering = ('-created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request)
