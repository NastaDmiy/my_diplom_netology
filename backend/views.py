import yaml

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import IntegrityError
from django.db.models import Q
from django.http import JsonResponse
from requests import get
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from .email import send_email
from .models import (
    Shop, Category, Product, ProductInfo, Parameter, ProductParameter,
    Contact, Order, OrderItem, ConfirmEmailToken,
)
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    ProductInfoSerializer, ContactSerializer,
    OrderSerializer, OrderConfirmSerializer,
)


# ============================================================
# Регистрация / вход / подтверждение email
# ============================================================

class RegisterAccount(APIView):
    """
    Регистрация нового пользователя (покупателя или магазина).
    POST: first_name, last_name, email, password, company, position, type
    """

    def post(self, request, *args, **kwargs):
        if {'first_name', 'last_name', 'email', 'password'} - set(request.data):
            return Response({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'Status': False, 'Errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            user = serializer.save()
        except IntegrityError:
            return Response({'Status': False, 'Errors': 'Пользователь с таким email уже существует'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Создаём токен подтверждения email
        token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user.id)
        send_email(
            subject=f'Подтверждение регистрации {user.email}',
            message=f'Ваш токен для подтверждения email: {token.key}',
            recipient_list=[user.email],
        )

        return Response({'Status': True})


class ConfirmAccount(APIView):
    """
    Подтверждение email по токену.
    POST: email, token
    """

    def post(self, request, *args, **kwargs):
        if {'email', 'token'} - set(request.data):
            return Response({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'},
                            status=status.HTTP_400_BAD_REQUEST)

        token = ConfirmEmailToken.objects.filter(
            user__email=request.data['email'],
            key=request.data['token'],
        ).first()

        if token:
            token.user.is_active = True
            token.user.save()
            token.delete()
            return Response({'Status': True})

        return Response({'Status': False, 'Errors': 'Неправильно указан токен или email'},
                        status=status.HTTP_400_BAD_REQUEST)


class LoginAccount(APIView):
    """
    Авторизация пользователя. Возвращает токен.
    POST: email, password
    """

    def post(self, request, *args, **kwargs):
        if {'email', 'password'} - set(request.data):
            return Response({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=request.data['email'],
                            password=request.data['password'])

        if user is not None:
            if not user.is_active:
                return Response({'Status': False, 'Errors': 'Пользователь не активирован'},
                                status=status.HTTP_403_FORBIDDEN)
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'Status': True, 'Token': token.key})

        return Response({'Status': False, 'Errors': 'Не удалось авторизоваться'},
                        status=status.HTTP_403_FORBIDDEN)


# ============================================================
# Импорт товаров от поставщика
# ============================================================

class PartnerUpdate(APIView):
    """
    Импорт прайса от поставщика.
    POST: url (ссылка на YAML-файл)
    """

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Log in required'},
                            status=status.HTTP_403_FORBIDDEN)

        if request.user.type != 'shop':
            return Response({'Status': False, 'Error': 'Только для магазинов'},
                            status=status.HTTP_403_FORBIDDEN)

        url = request.data.get('url')
        if not url:
            return Response({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'},
                            status=status.HTTP_400_BAD_REQUEST)

        validate_url = URLValidator()
        try:
            validate_url(url)
        except ValidationError as e:
            return Response({'Status': False, 'Error': str(e)},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            stream = get(url).content
            data = yaml.safe_load(stream)
        except Exception as e:
            return Response({'Status': False, 'Error': f'Ошибка загрузки: {e}'},
                            status=status.HTTP_400_BAD_REQUEST)

        shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=request.user.id)

        for category in data.get('categories', []):
            category_object, _ = Category.objects.get_or_create(
                id=category['id'], name=category['name'])
            category_object.shops.add(shop.id)
            category_object.save()

        ProductInfo.objects.filter(shop_id=shop.id).delete()

        for item in data.get('goods', []):
            product, _ = Product.objects.get_or_create(
                name=item['name'], category_id=item['category'])

            product_info = ProductInfo.objects.create(
                product_id=product.id,
                external_id=item['id'],
                model=item['model'],
                price=item['price'],
                price_rrc=item['price_rrc'],
                quantity=item['quantity'],
                shop_id=shop.id,
            )

            for name, value in item.get('parameters', {}).items():
                parameter_object, _ = Parameter.objects.get_or_create(name=name)
                ProductParameter.objects.create(
                    product_info_id=product_info.id,
                    parameter_id=parameter_object.id,
                    value=str(value),
                )

        return Response({'Status': True})


# ============================================================
# Каталог товаров
# ============================================================

class ProductInfoView(APIView):
    """
    Список товаров с фильтрацией.
    GET: ?shop_id=<id>&category_id=<id>&search=<строка>
    """

    def get(self, request, *args, **kwargs):
        query = Q(shop__state=True)
        shop_id = request.query_params.get('shop_id')
        category_id = request.query_params.get('category_id')

        if shop_id:
            query &= Q(shop_id=shop_id)
        if category_id:
            query &= Q(product__category_id=category_id)

        queryset = ProductInfo.objects.filter(query).select_related(
            'shop', 'product__category',
        ).prefetch_related('product_parameters__parameter').distinct()

        serializer = ProductInfoSerializer(queryset, many=True)
        return Response(serializer.data)


# ============================================================
# Корзина
# ============================================================

class BasketView(APIView):
    """
    Корзина покупателя.
    GET — получить содержимое корзины.
    POST — добавить товар(ы).  Тело: {"items": [{"product_info": 1, "quantity": 2}, ...]}
    PUT — изменить количество.  Тело: {"items": [{"product_info": 1, "quantity": 5}]}
    DELETE — удалить позицию(и). Тело: {"items": [{"product_info": 1}]}
    """

    def _get_basket(self, user):
        return Order.objects.filter(user=user, state='basket').first()

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Log in required'},
                            status=status.HTTP_403_FORBIDDEN)

        basket = self._get_basket(request.user)
        if not basket:
            return Response({'Status': True, 'items': []})

        serializer = OrderSerializer(basket)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Log in required'},
                            status=status.HTTP_403_FORBIDDEN)

        items = request.data.get('items')
        if not items:
            return Response({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'},
                            status=status.HTTP_400_BAD_REQUEST)

        basket, _ = Order.objects.get_or_create(user=request.user, state='basket')

        created_count = 0
        for item in items:
            product_info_id = item.get('product_info')
            quantity = item.get('quantity', 1)
            if not product_info_id:
                continue
            obj, created = OrderItem.objects.update_or_create(
                order=basket,
                product_info_id=product_info_id,
                defaults={'quantity': quantity},
            )
            if created:
                created_count += 1

        return Response({'Status': True, 'Created items': created_count})

    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Log in required'},
                            status=status.HTTP_403_FORBIDDEN)

        items = request.data.get('items')
        if not items:
            return Response({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'},
                            status=status.HTTP_400_BAD_REQUEST)

        basket = self._get_basket(request.user)
        if not basket:
            return Response({'Status': False, 'Errors': 'Корзина не найдена'},
                            status=status.HTTP_404_NOT_FOUND)

        updated = 0
        for item in items:
            product_info_id = item.get('product_info')
            quantity = item.get('quantity')
            if not product_info_id or quantity is None:
                continue
            updated += OrderItem.objects.filter(
                order=basket, product_info_id=product_info_id,
            ).update(quantity=quantity)

        return Response({'Status': True, 'Updated items': updated})

    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Log in required'},
                            status=status.HTTP_403_FORBIDDEN)

        items = request.data.get('items')
        if not items:
            return Response({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'},
                            status=status.HTTP_400_BAD_REQUEST)

        basket = self._get_basket(request.user)
        if not basket:
            return Response({'Status': False, 'Errors': 'Корзина не найдена'},
                            status=status.HTTP_404_NOT_FOUND)

        ids = [item.get('product_info') for item in items if item.get('product_info')]
        deleted, _ = OrderItem.objects.filter(
            order=basket, product_info_id__in=ids,
        ).delete()

        return Response({'Status': True, 'Deleted items': deleted})


# ============================================================
# Контакты
# ============================================================

class ContactView(APIView):
    """
    Управление контактами пользователя.
    GET — список.
    POST — добавить.
    PUT — изменить (id обязателен).
    DELETE — удалить (?id=<id> или в теле).
    """

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Log in required'},
                            status=status.HTTP_403_FORBIDDEN)
        contacts = Contact.objects.filter(user=request.user)
        serializer = ContactSerializer(contacts, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Log in required'},
                            status=status.HTTP_403_FORBIDDEN)

        if {'city', 'street', 'phone'} - set(request.data):
            return Response({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = ContactSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({'Status': True})
        return Response({'Status': False, 'Errors': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Log in required'},
                            status=status.HTTP_403_FORBIDDEN)

        contact_id = request.data.get('id')
        if not contact_id:
            return Response({'Status': False, 'Errors': 'Не указан id контакта'},
                            status=status.HTTP_400_BAD_REQUEST)

        contact = Contact.objects.filter(id=contact_id, user=request.user).first()
        if not contact:
            return Response({'Status': False, 'Errors': 'Контакт не найден'},
                            status=status.HTTP_404_NOT_FOUND)

        serializer = ContactSerializer(contact, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'Status': True})
        return Response({'Status': False, 'Errors': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Log in required'},
                            status=status.HTTP_403_FORBIDDEN)

        contact_id = request.data.get('id') or request.query_params.get('id')
        if not contact_id:
            return Response({'Status': False, 'Errors': 'Не указан id контакта'},
                            status=status.HTTP_400_BAD_REQUEST)

        deleted, _ = Contact.objects.filter(id=contact_id, user=request.user).delete()
        return Response({'Status': True, 'Deleted': deleted})


# ============================================================
# Заказы
# ============================================================

class OrderView(APIView):
    """
    GET  — список заказов покупателя (кроме корзины).
    POST — подтвердить заказ из корзины.  Тело: {"contact_id": <id>}
    """

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Log in required'},
                            status=status.HTTP_403_FORBIDDEN)

        orders = Order.objects.filter(user=request.user).exclude(state='basket')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Log in required'},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = OrderConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'Status': False, 'Errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)

        contact_id = serializer.validated_data['contact_id']
        contact = Contact.objects.filter(id=contact_id, user=request.user).first()
        if not contact:
            return Response({'Status': False, 'Errors': 'Контакт не найден'},
                            status=status.HTTP_404_NOT_FOUND)

        basket = Order.objects.filter(user=request.user, state='basket').first()
        if not basket or not basket.ordered_items.exists():
            return Response({'Status': False, 'Errors': 'Корзина пуста'},
                            status=status.HTTP_400_BAD_REQUEST)

        basket.state = 'new'
        basket.contact = contact
        basket.save()

        # Письмо покупателю
        send_email(
            subject='Заказ оформлен',
            message=f'Ваш заказ №{basket.id} успешно оформлен. Сумма: '
                    f'{sum(i.product_info.price * i.quantity for i in basket.ordered_items.all())}',
            recipient_list=[request.user.email],
        )

        return Response({'Status': True, 'Order id': basket.id})