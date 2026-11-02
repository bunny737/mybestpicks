from django.urls import path

from . import views

urlpatterns = [
    path("", views.subscribe, name="subscribe"),
    path("confirm/<str:token>/", views.confirm, name="subscribe_confirm"),
    path("unsubscribe/<str:token>/", views.unsubscribe, name="subscribe_unsubscribe"),
]
