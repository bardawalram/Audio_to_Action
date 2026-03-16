import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.fees.models import FeePayment
from apps.fees.notifications import send_fee_payment_whatsapp

logger = logging.getLogger(__name__)


@receiver(post_save, sender=FeePayment)
def notify_fee_payment(sender, instance, created, **kwargs):
    """Send WhatsApp notification when a new fee payment is created."""
    if not created:
        return

    if instance.payment_status not in (
        FeePayment.PaymentStatus.PAID,
        FeePayment.PaymentStatus.PARTIAL,
    ):
        return

    send_fee_payment_whatsapp(instance)
