from django.urls import path
from . import views

app_name = 'books'

urlpatterns = [
    path('', views.book_search, name='search'),
    path('health/', views.health_check, name='health'),
]
