from django.urls import path
from .views import *


urlpatterns = [
    path('',view=main, name='main'),
]