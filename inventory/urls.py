from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(
        template_name='inventory/registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('clients/', views.client_list, name='client_list'),
    path('client/<int:pk>/', views.client_detail, name='client_detail'),
    path('parts/', views.part_list, name='part_list'),
    path('add-to-quote/<int:part_id>/', views.add_to_quote, name='add_to_quote'),
    path('delete-quote/<int:quote_id>/',
         views.delete_quote, name='delete_quote'),
    path('view-quote/', views.view_quote, name='view_quote'),
    path('clear-quote/', views.clear_quote, name='clear_quote'),
    path('remove-from-quote/<int:part_id>/',
         views.remove_from_quote, name='remove_from_quote'),
    path('finalize-quote/', views.finalize_quote, name='finalize_quote'),
    path('generate-pdf/', views.generate_pdf_quote, name='generate_pdf'),
    path('reprint-pdf/<int:quote_id>/', views.reprint_pdf, name='reprint_pdf'),
]
