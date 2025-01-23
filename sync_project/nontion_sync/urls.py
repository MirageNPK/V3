from django.urls import path
from . import views

urlpatterns = [
    path('api/run-task/', views.run_task, name='run_task'),
]