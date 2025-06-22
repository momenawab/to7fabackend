from django.urls import path
from . import views

urlpatterns = [
    path('', views.notification_list, name='notification_list'),
    path('<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('read-all/', views.mark_all_read, name='mark_all_read'),
] 