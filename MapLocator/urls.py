from django.contrib import admin
from django.urls import path
from . import views


urlpatterns = [
    path('',views.map_locator),
    path('analysis/',views.analysis)

]