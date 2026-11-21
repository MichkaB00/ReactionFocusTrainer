from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Фокус — адміністрування"
admin.site.site_title = "Фокус"
admin.site.index_title = "Керування застосунком"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("users/", include("users.urls")),
    path("", include("training.urls")),
]
