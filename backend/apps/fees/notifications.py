import logging
import re
import threading

from django.conf import settings

logger = logging.getLogger(__name__)


def send_fee_payment_whatsapp(payment):
    """
    Send a WhatsApp notification for a fee payment.
    Spawns a daemon thread so the main request is never blocked.
    """
    if not getattr(settings, 'WHATSAPP_NOTIFICATIONS_ENABLED', False):
        return

    student = payment.student
    phone = getattr(student, 'phone_number', None)

    if not phone:
        logger.info(
            "No phone number for student %s (payment %s), skipping WhatsApp notification",
            student.id, payment.receipt_number,
        )
        return

    formatted = _format_whatsapp_number(phone)
    if not formatted:
        logger.warning(
            "Invalid phone number '%s' for student %s, skipping WhatsApp notification",
            phone, student.id,
        )
        return

    thread = threading.Thread(
        target=_send_whatsapp_message,
        args=(payment, formatted),
        daemon=True,
    )
    thread.start()


def _send_whatsapp_message(payment, whatsapp_number):
    """
    Sends the WhatsApp message via Twilio. Runs in a background thread.
    Catches all exceptions so it never affects the main request.
    """
    try:
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN

        body = _build_payment_message(payment)

        if not account_sid or not auth_token:
            # Console mode: print message instead of sending via Twilio
            print("\n" + "=" * 50)
            print(" WHATSAPP NOTIFICATION (console mode)")
            print(" Twilio not configured — printing instead")
            print("=" * 50)
            print(f" To: {whatsapp_number}")
            print(f" From: {settings.TWILIO_WHATSAPP_FROM}")
            print("-" * 50)
            print(body)
            print("=" * 50 + "\n")
            logger.info(
                "WhatsApp notification printed to console for payment %s (Twilio not configured)",
                payment.receipt_number,
            )
            return

        from twilio.rest import Client

        client = Client(account_sid, auth_token)

        message = client.messages.create(
            from_=settings.TWILIO_WHATSAPP_FROM,
            to=whatsapp_number,
            body=body,
        )

        logger.info(
            "WhatsApp notification sent for payment %s (SID: %s)",
            payment.receipt_number, message.sid,
        )

    except Exception:
        logger.exception(
            "Failed to send WhatsApp notification for payment %s",
            payment.receipt_number,
        )


def _format_whatsapp_number(phone):
    """
    Normalize an Indian phone number to whatsapp:+91XXXXXXXXXX format.
    Returns None if the number cannot be parsed.
    """
    if not phone:
        return None

    digits = re.sub(r'\D', '', phone)

    # 10-digit Indian mobile number
    if len(digits) == 10 and digits[0] in '6789':
        return f"whatsapp:+91{digits}"

    # 12-digit with 91 country code
    if len(digits) == 12 and digits.startswith('91'):
        return f"whatsapp:+{digits}"

    # Already E.164 with country code (e.g. +919876543210 → 919876543210)
    if len(digits) == 12 and digits.startswith('91') and digits[2] in '6789':
        return f"whatsapp:+{digits}"

    # Handle numbers with leading + already stripped
    if phone.startswith('+') and len(digits) >= 10:
        return f"whatsapp:+{digits}"

    return None


def _build_payment_message(payment):
    """Build the WhatsApp message body for a fee payment."""
    student = payment.student
    fee_structure = payment.fee_structure

    student_name = student.get_full_name()
    fee_type = fee_structure.get_fee_type_display()
    term = fee_structure.get_term_display()
    method = payment.get_payment_method_display()
    status = payment.get_payment_status_display()
    date_str = payment.payment_date.strftime('%d/%m/%Y')
    amount = f"Rs. {payment.amount_paid:,.0f}" if payment.amount_paid == int(payment.amount_paid) else f"Rs. {payment.amount_paid:,.2f}"

    return (
        f"Fee Payment Confirmation\n"
        f"============================\n"
        f"\n"
        f"Student: {student_name}\n"
        f"Receipt No: {payment.receipt_number}\n"
        f"Amount: {amount}\n"
        f"Fee Type: {fee_type}\n"
        f"Term: {term}\n"
        f"Payment Method: {method}\n"
        f"Date: {date_str}\n"
        f"Status: {status}\n"
        f"\n"
        f"Thank you for the payment."
    )
