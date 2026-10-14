from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.mail import send_mail
from django.conf import settings

from .models import (
    User, Shop, Category, Product, ProductInfo, Parameter,
    ProductParameter, Contact, Order, OrderItem, ConfirmEmailToken,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('id', 'email', 'first_name', 'last_name', 'type', 'is_active', 'is_staff')
    list_filter = ('type', 'is_active', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name', 'company')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Персональные данные', {'fields': ('first_name', 'last_name', 'company', 'position')}),
        ('Права', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Тип', {'fields': ('type',)}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'type'),
        }),
    )


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user', 'state')
    list_filter = ('state',)
    search_fields = ('name',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    filter_horizontal = ('shops',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category')
    list_filter = ('category',)
    search_fields = ('name',)


class ProductParameterInline(admin.TabularInline):
    model = ProductParameter
    extra = 1


@admin.register(ProductInfo)
class ProductInfoAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'shop', 'model', 'quantity', 'price', 'price_rrc')
    list_filter = ('shop', 'product__category')
    search_fields = ('product__name', 'model', 'external_id')
    inlines = (ProductParameterInline,)
    autocomplete_fields = ('product', 'shop')


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(ProductParameter)
class ProductParameterAdmin(admin.ModelAdmin):
    list_display = ('id', 'product_info', 'parameter', 'value')
    list_filter = ('parameter',)
    search_fields = ('value',)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'city', 'street', 'house', 'phone')
    search_fields = ('city', 'street', 'phone', 'user__email')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    autocomplete_fields = ('product_info',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'dt', 'state', 'contact')
    list_filter = ('state', 'dt')
    search_fields = ('user__email',)
    inlines = (OrderItemInline,)

    def save_model(self, request, obj, form, change):
        """При изменении статуса заказа отправляем письмо покупателю."""
        old_state = None
        if change:
            old_state = Order.objects.get(pk=obj.pk).state

        super().save_model(request, obj, form, change)

        if change and old_state != obj.state:
            send_mail(
                subject=f'Статус заказа №{obj.id} изменён',
                message=(
                    f'Ваш заказ №{obj.id} перешёл в статус: {obj.get_state_display()}.\n'
                    f'Текущий статус: {obj.state}'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[obj.user.email],
                fail_silently=True,
            )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product_info', 'quantity')
    search_fields = ('order__id', 'product_info__product__name')


@admin.register(ConfirmEmailToken)
class ConfirmEmailTokenAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'key', 'created_at')
    search_fields = ('user__email', 'key')
    readonly_fields = ('key', 'created_at')