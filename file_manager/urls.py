from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='file_manager-home'),
    path('<int:invoice>/', views.order_details, name='file_manager-order_details'),
    path('orders/', views.display_orders, name='file_manager-display_orders'),
    path('storage/', views.storage, name='file_manager-storage'),
    path('new_customer/', views.customer_form, name='file_manager-customer_form'),
    path('new_order/', views.rental_order_form, name='file_manager-rental_order_form'),
    path('update_order/<int:pk>', views.update_order_form, name='file_manager-update_order_form'),
    path('delete_order/<int:pk>', views.delete_order, name='file_manager-delete_order'),
    path('new_search/', views.new_search, name='file_manager-new_search'),
    path('web_orders/', views.web_orders, name='file_manager-web_orders'),
    path('export/<int:invoice>', views.export_order_file, name='file_manager-export_order'),
    path('webhook/', views.webhook),

    path('login/', views.login_page, name='file_manager-login'),
    path('register/', views.register_page, name='file_manager-register'),
    path('logout/', views.logout_user, name='file_manager-logout'),

    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password_reset_confirm/<uidb64>/<token>', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password_reset_complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

]