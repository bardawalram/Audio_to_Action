"""
Tests for WhatsApp fee payment notifications.
Run: python manage.py test apps.fees.tests
"""
from datetime import date
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings

from apps.academics.models import Class, Section, ClassSection, Student
from apps.fees.models import FeeStructure, FeePayment
from apps.fees.notifications import (
    send_fee_payment_whatsapp,
    _format_whatsapp_number,
    _build_payment_message,
)


TWILIO_SETTINGS = {
    'WHATSAPP_NOTIFICATIONS_ENABLED': True,
    'TWILIO_ACCOUNT_SID': 'ACtest1234567890',
    'TWILIO_AUTH_TOKEN': 'test_auth_token',
    'TWILIO_WHATSAPP_FROM': 'whatsapp:+14155238886',
}


class PhoneNumberFormattingTest(TestCase):
    """Test _format_whatsapp_number with various input formats."""

    def test_10_digit_indian_number(self):
        self.assertEqual(_format_whatsapp_number('9876543210'), 'whatsapp:+919876543210')

    def test_12_digit_with_country_code(self):
        self.assertEqual(_format_whatsapp_number('919876543210'), 'whatsapp:+919876543210')

    def test_plus_prefix(self):
        self.assertEqual(_format_whatsapp_number('+919876543210'), 'whatsapp:+919876543210')

    def test_with_spaces_and_dashes(self):
        self.assertEqual(_format_whatsapp_number('98-765-43210'), 'whatsapp:+919876543210')

    def test_empty_string(self):
        self.assertIsNone(_format_whatsapp_number(''))

    def test_none(self):
        self.assertIsNone(_format_whatsapp_number(None))

    def test_too_short(self):
        self.assertIsNone(_format_whatsapp_number('12345'))

    def test_landline_rejected(self):
        """Indian landline numbers starting with 0 or 1-5 should be rejected."""
        self.assertIsNone(_format_whatsapp_number('0226543210'))


class MessageFormattingTest(TestCase):
    """Test _build_payment_message output."""

    def setUp(self):
        cls = Class.objects.create(name='9th', grade_number=9)
        sec = Section.objects.create(name='A')
        cs = ClassSection.objects.create(class_obj=cls, section=sec, academic_year='2025-2026')
        self.student = Student.objects.create(
            first_name='Arun', last_name='Garde',
            roll_number=1, class_section=cs,
            date_of_birth=date(2010, 5, 15),
            phone_number='9876543210',
        )
        self.fee_structure = FeeStructure.objects.create(
            class_obj=cls,
            fee_type=FeeStructure.FeeType.TUITION,
            term=FeeStructure.Term.TERM_1,
            amount=Decimal('5000.00'),
        )

    def test_message_contains_student_name(self):
        payment = FeePayment.objects.create(
            student=self.student,
            fee_structure=self.fee_structure,
            amount_paid=Decimal('5000'),
        )
        msg = _build_payment_message(payment)
        self.assertIn('Arun Garde', msg)
        self.assertIn('Rs. 5,000', msg)
        self.assertIn('Tuition Fee', msg)
        self.assertIn('Term 1', msg)
        self.assertIn('Cash', msg)
        self.assertIn('Paid', msg)
        self.assertIn(payment.receipt_number, msg)


class SignalTest(TestCase):
    """Test that post_save signal triggers WhatsApp notification."""

    def setUp(self):
        cls = Class.objects.create(name='10th', grade_number=10)
        sec = Section.objects.create(name='B')
        cs = ClassSection.objects.create(class_obj=cls, section=sec, academic_year='2025-2026')
        self.student = Student.objects.create(
            first_name='Ravi', last_name='Kumar',
            roll_number=2, class_section=cs,
            date_of_birth=date(2010, 3, 20),
            phone_number='9123456789',
        )
        self.fee_structure = FeeStructure.objects.create(
            class_obj=cls,
            fee_type=FeeStructure.FeeType.EXAM,
            term=FeeStructure.Term.TERM_1,
            amount=Decimal('1000.00'),
        )

    @override_settings(**TWILIO_SETTINGS)
    @patch('apps.fees.notifications.threading.Thread')
    def test_signal_fires_on_paid_payment(self, mock_thread_cls):
        """Creating a PAID payment should spawn a notification thread."""
        mock_thread = MagicMock()
        mock_thread_cls.return_value = mock_thread

        FeePayment.objects.create(
            student=self.student,
            fee_structure=self.fee_structure,
            amount_paid=Decimal('1000'),
            payment_status=FeePayment.PaymentStatus.PAID,
        )

        mock_thread_cls.assert_called_once()
        mock_thread.start.assert_called_once()

    @override_settings(**TWILIO_SETTINGS)
    @patch('apps.fees.notifications.threading.Thread')
    def test_signal_fires_on_partial_payment(self, mock_thread_cls):
        """Creating a PARTIAL payment should also send notification."""
        mock_thread = MagicMock()
        mock_thread_cls.return_value = mock_thread

        FeePayment.objects.create(
            student=self.student,
            fee_structure=self.fee_structure,
            amount_paid=Decimal('500'),
            payment_status=FeePayment.PaymentStatus.PARTIAL,
        )

        mock_thread_cls.assert_called_once()
        mock_thread.start.assert_called_once()

    @override_settings(**TWILIO_SETTINGS)
    @patch('apps.fees.notifications.threading.Thread')
    def test_signal_skips_pending_payment(self, mock_thread_cls):
        """PENDING payments should not trigger notification."""
        FeePayment.objects.create(
            student=self.student,
            fee_structure=self.fee_structure,
            amount_paid=Decimal('0'),
            payment_status=FeePayment.PaymentStatus.PENDING,
        )

        mock_thread_cls.assert_not_called()

    @override_settings(WHATSAPP_NOTIFICATIONS_ENABLED=False)
    @patch('apps.fees.notifications.threading.Thread')
    def test_signal_skips_when_disabled(self, mock_thread_cls):
        """No notification when feature is disabled."""
        FeePayment.objects.create(
            student=self.student,
            fee_structure=self.fee_structure,
            amount_paid=Decimal('1000'),
            payment_status=FeePayment.PaymentStatus.PAID,
        )

        mock_thread_cls.assert_not_called()

    @override_settings(**TWILIO_SETTINGS)
    @patch('apps.fees.notifications.threading.Thread')
    def test_signal_skips_no_phone(self, mock_thread_cls):
        """No notification when student has no phone number."""
        self.student.phone_number = ''
        self.student.save()

        FeePayment.objects.create(
            student=self.student,
            fee_structure=self.fee_structure,
            amount_paid=Decimal('1000'),
            payment_status=FeePayment.PaymentStatus.PAID,
        )

        mock_thread_cls.assert_not_called()


class TwilioIntegrationTest(TestCase):
    """Test the actual Twilio client call (mocked)."""

    def setUp(self):
        # Disconnect signal so we can test _send_whatsapp_message in isolation
        from django.db.models.signals import post_save
        from apps.fees.signals import notify_fee_payment
        post_save.disconnect(notify_fee_payment, sender=FeePayment)

        cls = Class.objects.create(name='8th', grade_number=8)
        sec = Section.objects.create(name='C')
        cs = ClassSection.objects.create(class_obj=cls, section=sec, academic_year='2025-2026')
        self.student = Student.objects.create(
            first_name='Priya', last_name='Sharma',
            roll_number=3, class_section=cs,
            date_of_birth=date(2011, 8, 10),
            phone_number='9876543210',
        )
        self.fee_structure = FeeStructure.objects.create(
            class_obj=cls,
            fee_type=FeeStructure.FeeType.TRANSPORT,
            term=FeeStructure.Term.ANNUAL,
            amount=Decimal('12000.00'),
        )

    def tearDown(self):
        from django.db.models.signals import post_save
        from apps.fees.signals import notify_fee_payment
        post_save.connect(notify_fee_payment, sender=FeePayment)

    @override_settings(**TWILIO_SETTINGS)
    @patch('twilio.rest.Client')
    def test_twilio_client_called_correctly(self, mock_client_cls):
        """Verify Twilio Client is created with correct credentials and message is sent."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(sid='SM_TEST_123')

        payment = FeePayment.objects.create(
            student=self.student,
            fee_structure=self.fee_structure,
            amount_paid=Decimal('12000'),
        )

        from apps.fees.notifications import _send_whatsapp_message
        _send_whatsapp_message(payment, 'whatsapp:+919876543210')

        mock_client_cls.assert_called_once_with('ACtest1234567890', 'test_auth_token')
        mock_client.messages.create.assert_called_once()

        call_kwargs = mock_client.messages.create.call_args[1]
        self.assertEqual(call_kwargs['from_'], 'whatsapp:+14155238886')
        self.assertEqual(call_kwargs['to'], 'whatsapp:+919876543210')
        self.assertIn('Priya Sharma', call_kwargs['body'])
        self.assertIn('Transport Fee', call_kwargs['body'])
