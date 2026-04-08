from django.urls import path
from django.contrib.auth import views as auth_views
from .views.customers import dashboard, register, client_list, client_detail
from .views.inventory import part_list, add_to_quote, view_quote, clear_quote, remove_from_quote
from .views.orders import finalize_quote, delete_quote, generate_pdf_quote, reprint_pdf

urlpatterns = [
    # --- CUSTOMERS & AUTH ---
    path('', dashboard, name='dashboard'),
    path('register/', register, name='register'),
    path('login/', auth_views.LoginView.as_view(
        template_name='inventory/registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('clients/', client_list, name='client_list'),
    path('client/<int:pk>/', client_detail, name='client_detail'),

    # --- INVENTORY ---
    path('parts/', part_list, name='part_list'),
    path('add-to-quote/<int:part_id>/', add_to_quote, name='add_to_quote'),
    path('view-quote/', view_quote, name='view_quote'),
    path('clear-quote/', clear_quote, name='clear_quote'),
    path('remove-from-quote/<int:part_id>/',
         remove_from_quote, name='remove_from_quote'),

    # --- ORDERS ---
    path('delete-quote/<int:quote_id>/', delete_quote, name='delete_quote'),
    path('finalize-quote/', finalize_quote, name='finalize_quote'),
    path('generate-pdf/', generate_pdf_quote, name='generate_pdf'),
    path('reprint-pdf/<int:quote_id>/', reprint_pdf, name='reprint_pdf'),
]
