from django.urls import path
from . import views

urlpatterns = [
    path('products/', views.products , name='products'),
    path('product_detail/<slug:slug>/', views.product_detail , name='product_detail'),
    path('add_item/', views.add_item , name='add_item'),
    path('product_is_added/', views.product_is_added , name='product_is_added'),
    path('get_cart/', views.get_cart , name='get_cart'),
    path('update_quantity/<int:item_id>/', views.update_quantity , name='update_quantity'),
    path('delete_item/<int:item_id>/', views.delete_item , name='delete_item'),
    path('user_info/', views.user_info , name='user_info'),
    path('signup/', views.signup , name='signup'),
    path('update_profile/', views.update_profile , name='update_profile'),
    path('clear_cart/', views.clear_cart , name='clear_cart'),
    path('complete_order/', views.complete_order , name='complete_order'),
    path('verify_payment/', views.verify_payment , name='verify_payment'),
    path('order_detail/<str:order_id>/', views.order_detail , name='order_detail'),
    path('user_orders/', views.user_orders , name='user_orders'),
   

]   
