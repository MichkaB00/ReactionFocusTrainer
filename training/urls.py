from django.urls import path

from . import views

app_name = "training"

urlpatterns = [
    path("", views.TrainingModeListView.as_view(), name="home"),
    path("training/reaction/", views.reaction, name="reaction"),
    path("training/concentration/", views.concentration, name="concentration"),
    path("statistics/", views.statistics, name="statistics"),
    path("training/save/", views.save_result, name="save_result"),
]
