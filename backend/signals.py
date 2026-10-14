from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver
from django_rest_passwordreset.signals import reset_password_token_created

from .models import ConfirmEmailToken, User


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, **kwargs):
    """
    Отправка письма с токеном для сброса пароля.
    Срабатывает при POST /api/v1/user/password_reset.
    """
    send_email(
        subject=f'Сброс пароля для {reset_password_token.user.email}',
        message=(
            f'Здравствуйте!\n\n'
            f'Вы запросили сброс пароля на сервисе заказа товаров.\n'
            f'Ваш токен для сброса пароля: {reset_password_token.key}\n\n'
            f'Если вы не запрашивали сброс — просто проигнорируйте это письмо.'
        ),
        recipient_list=[reset_password_token.user.email],
    )


def send_email(subject: str, message: str, recipient_list: list):
    """Отправка email через настроенный backend (по умолчанию — console)."""
    msg = EmailMultiAlternatives(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipient_list,
    )
    msg.send()