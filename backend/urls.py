from django.urls import path

from .views import (
    RegisterAccount, ConfirmAccount, LoginAccount,
    PartnerUpdate, ProductInfoView, BasketView, ContactView, OrderView,
)

urlpatterns = [
    path('user/register', RegisterAccount.as_view(), name='user-register'),
    path('user/register/confirm', ConfirmAccount.as_view(), name='user-register-confirm'),
    path('user/login', LoginAccount.as_view(), name='user-login'),

    path('partner/update', PartnerUpdate.as_view(), name='partner-update'),

    path('products', ProductInfoView.as_view(), name='products'),

    path('basket', BasketView.as_view(), name='basket'),

    path('contact', ContactView.as_view(), name='contact'),

    path('order', OrderView.as_view(), name='order'),
]

from .views import (
    RegisterAccount, ConfirmAccount, LoginAccount,
    PartnerUpdate, PartnerState, PartnerOrders,
    ProductInfoView, BasketView, ContactView, OrderView,
    CategoryView, ShopView,
)

urlpatterns = [
    path('user/register', RegisterAccount.as_view(), name='user-register'),
    path('user/register/confirm', ConfirmAccount.as_view(), name='user-register-confirm'),
    path('user/login', LoginAccount.as_view(), name='user-login'),

    path('partner/update', PartnerUpdate.as_view(), name='partner-update'),
    path('partner/state', PartnerState.as_view(), name='partner-state'),
    path('partner/orders', PartnerOrders.as_view(), name='partner-orders'),

    path('products', ProductInfoView.as_view(), name='products'),
    path('basket', BasketView.as_view(), name='basket'),
    path('contact', ContactView.as_view(), name='contact'),
    path('order', OrderView.as_view(), name='order'),

    path('products', ProductInfoView.as_view(), name='products'),
    path('categories', CategoryView.as_view(), name='categories'),
    path('shops', ShopView.as_view(), name='shops'),
]