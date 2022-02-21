from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('<int:invoice>/', views.order_details, name='order_details'),
    path('orders/', views.display_orders, name='display_orders'),
    path('storage/', views.storage, name='storage'),
    path('new_customer/', views.customer_form, name='customer_form'),
    path('new_order/', views.rental_order_form, name='rental_order_form'),

    path('update_order/<int:pk>', views.update_order_form, name='update_order_form'),
    path('delete_order/<int:pk>', views.delete_order, name='delete_order'),
    # path('create_events/<int:invoice>', views.create_events, name='create_events'),

    path('new_search/', views.new_search, name='new_search'),
    path('export/<int:invoice>', views.export_order_file, name='export_order'),

    path('login/', views.login_page, name='login'),
    path('register/', views.register_page, name='register'),
    path('logout/', views.logout_user, name='logout'),

    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password_reset_confirm/<uidb64>/<token>', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password_reset_complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    path('webhook/test-order', views.test_order, name='webhook_order'),

]