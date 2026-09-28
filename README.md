# Backend-приложение для автоматизации закупок

Дипломный проект курса «Python-разработчик: расширенный курс» (Netology).

Backend на Django REST Framework для сервиса заказа товаров из нескольких магазинов.

## Возможности

- Регистрация пользователя с подтверждением email (покупатель / магазин).
- Авторизация по токену.
- Импорт прайс-листов магазина из YAML-файла по URL.
- Каталог товаров с фильтрацией по магазину и категории.
- Корзина: добавление, изменение, удаление товаров.
- Контакты пользователя (адрес доставки).
- Оформление заказа с отправкой email покупателю.
- Просмотр списка заказов.

## Стек

- Python 3.10+
- Django 4.2
- Django REST Framework
- django-rest-passwordreset
- PyYAML, requests

## Установка

    git clone <URL_репозитория>
    cd orders
    python -m venv env
    source env/Scripts/activate    # Windows (Git Bash)
    # source env/bin/activate      # Linux/macOS
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py runserver

## API

Базовый префикс: /api/v1/

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | /user/register | Регистрация |
| POST | /user/register/confirm | Подтверждение email |
| POST | /user/login | Авторизация (возвращает токен) |
| POST | /partner/update | Импорт товаров магазина по URL YAML |
| GET | /products | Каталог товаров (фильтры shop_id, category_id) |
| GET/POST/PUT/DELETE | /basket | Корзина |
| GET/POST/PUT/DELETE | /contact | Контакты |
| GET/POST | /order | Заказы (список / подтверждение) |

Авторизация — заголовок Authorization: Token <token>.

## Формат YAML для импорта

    shop: Название магазина
    categories:
      - id: 1
        name: Категория
    goods:
      - id: 123
        category: 1
        model: vendor/model
        name: Название товара
        price: 1000
        price_rrc: 1200
        quantity: 5
        parameters:
          "Цвет": красный
