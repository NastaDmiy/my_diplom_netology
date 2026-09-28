from django.core.mail import EmailMultiAlternatives
from django.conf import settings


def send_email(subject: str, message: str, recipient_list: list[str]):
    """Отправляет email. При console-бэкенде просто печатает в терминал."""
    msg = EmailMultiAlternatives(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipient_list,
    )
    msg.send()