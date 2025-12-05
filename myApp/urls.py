from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('save-bill/', views.save_bill_view, name='save-bill'),
    path('print-bill/<int:bill_id>/', views.print_bill_view, name='print-bill'),
    path('create-kot/', views.create_kot_view, name='create-kot'),
    path('print-kot/<int:kot_id>/', views.print_kot_view, name='print-kot'),
    path('reports/', views.report_view, name='reports'),


]