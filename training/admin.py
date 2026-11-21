from django.contrib import admin

from .models import TrainingMode


@admin.register(TrainingMode)
class TrainingModeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "description")

    def get_readonly_fields(self, request, obj=None):
        return ("slug",) if obj else ()
