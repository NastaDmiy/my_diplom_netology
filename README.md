# Backend-приложение для автоматизации закупок

Дипломный проект курса «Python-разработчик: расширенный курс» (Netology).

Backend на Django REST Framework для сервиса заказа товаров из нескольких магазинов.

## Возможности

- Регистрация пользователя с подтверждением email (покупатель / магазин).
- Авторизация по токену.
- Восстановление пароля по email.
- Импорт прайс-листов магазина из YAML-файла по URL.
- Каталог товаров с фильтрацией по магазину, категории и поиску по названию.
- Корзина: добавление, изменение, удаление товаров.
- Контакты пользователя (адрес доставки).
- Оформление заказа с отправкой email покупателю и администратору (накладная).
- Управление статусом заказа с уведомлением покупателя (админка и API).
- Просмотр списка заказов и деталей отдельного заказа.
- Эндпоинты для поставщика: импорт прайса, включение/отключение приёма заказов, список заказов с товарами магазина.
- Просмотр и редактирование профиля пользователя.
- Документация API (Swagger UI).

## Стек

- Python 3.10+
- Django 4.2
- Django REST Framework
- django-rest-passwordreset
- drf-spectacular
- PyYAML, requests

## Установка

```bash
git clone <URL_репозитория>
cd orders
python -m venv env
source env/Scripts/activate    # Windows (Git Bash)
# source env/bin/activate      # Linux/macOS
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

> **Важно (Windows):** после правок `urls.py`, `settings.py`, `apps.py` сервер может
> не подхватить изменения из-за нестабильного `StatReloader`. Используйте
> `python manage.py runserver --noreload` и перезапускайте сервер вручную.

## Документация API

- Swagger UI: `http://127.0.0.1:8000/api/docs/`
- OpenAPI-схема (YAML): `http://127.0.0.1:8000/api/schema/`

## API

Базовый префикс: `/api/v1/`

Авторизация — заголовок `Authorization: Token <token>`.

### Пользователь

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/user/register` | Регистрация |
| POST | `/user/register/confirm` | Подтверждение email по токену |
| POST | `/user/login` | Авторизация (возвращает токен) |
| GET | `/user/details` | Профиль текущего пользователя |
| PUT | `/user/details` | Редактирование профиля (first_name, last_name, company, position) |
| POST | `/user/password_reset` | Запросить токен сброса пароля (**без слэша**) |
| POST | `/user/password_reset/confirm/` | Установить новый пароль (**со слэшем**) |
| POST | `/user/password_reset/validate_token/` | Проверить токен сброса |

### Каталог

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/products` | Каталог товаров. Параметры: `shop_id`, `category_id`, `search` |
| GET | `/categories` | Список категорий |
| GET | `/shops` | Список активных магазинов |

### Корзина, контакты, заказы

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET/POST/PUT/DELETE | `/basket` | Корзина |
| GET/POST/PUT/DELETE | `/contact` | Контакты (адреса доставки) |
| GET | `/order` | Список заказов пользователя |
| POST | `/order` | Подтвердить заказ (тело: `{"contact_id": 1}`) |
| GET | `/order/<id>` | Детали заказа |
| PUT | `/order/<id>/status` | Смена статуса заказа (только магазин) |

### Поставщик

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/partner/update` | Импорт прайса из YAML по URL |
| GET/POST | `/partner/state` | Получить/установить флаг приёма заказов |
| GET | `/partner/orders` | Список заказов, содержащих товары магазина |

## Пример импорта товаров

```bash
curl -X POST http://127.0.0.1:8000/api/v1/partner/update \
  -H "Authorization: Token <TOKEN_МАГАЗИНА>" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/shop1.yaml"}'
```

Формат YAML:

```yaml
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
```

## Админка

Доступна по адресу `http://127.0.0.1:8000/admin/`.

Реализовано:

- все модели зарегистрированы с `list_display`, фильтрами и поиском;
- `ProductParameterInline` для удобного редактирования параметров товара;
- `OrderItemInline` в заказе;
- при изменении статуса заказа в админке покупателю автоматически отправляется email.

> Если после `createsuperuser` админка не пускает — проверьте, что
> `is_active=True` у пользователя. В `UserManager.create_superuser` это
> значение выставляется автоматически (см. `backend/models.py`).

## Email

Для разработки используется `console`-бэкенд — письма печатаются в терминал
`runserver`. Для продакшена замените настройки в `orders/settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.example.com'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'your@email.com'
EMAIL_HOST_PASSWORD = 'your_password'
ADMIN_EMAIL = EMAIL_HOST_USER   # адрес для накладных по заказам
```

## Безопасность (для продакшена)

В учебном проекте `SECRET_KEY` и `ALLOWED_HOSTS = ['*']` заданы открыто —
для реального развёртывания их нужно вынести в переменные окружения
и ограничить список разрешённых хостов.

## Автор

Дмитриева Анастасия, 2026