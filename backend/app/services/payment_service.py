from datetime import datetime
from app import db
from app.models import Payment, PaymentStatus, PaymentMethod
from app.services.stripe_payment_service import StripePaymentService
from app.schemas.donation_schemas import DonationSchema
from app.schemas.payment_schemas import PaymentDetailsSchema, RefundSchema
from app.config import StripeConfig
from app.utils.redis_client import get_redis_client
import logging
from marshmallow import ValidationError

logger = logging.getLogger(__name__)

class PaymentService:
    def __init__(self):
        self.stripe_service = StripePaymentService()
        self.donation_schema = DonationSchema()
        self.payment_details_schema = PaymentDetailsSchema()
        self.refund_schema = RefundSchema()
        self.redis_client = get_redis_client()

    async def validate_payment_request(self, amount: float, currency: str) -> None:
        """Validate payment amount and currency"""
        if currency not in StripeConfig.SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency: {currency}")
        
        min_amount = StripeConfig.MINIMUM_AMOUNT.get(currency, 0.5)
        if amount < min_amount:
            raise ValueError(f"Amount below minimum for {currency}: {min_amount}")

    async def create_payment(self, user_id, donation_id, amount, currency, payment_method, ip_address=None):
        """Create a new payment with validation and rate limiting."""
        try:
            validated_data = self.donation_schema.load({
                "user_id": user_id, "donation_id": donation_id, "amount": amount, "currency": currency, "payment_method": payment_method
            })

            await self.validate_payment_request(validated_data['amount'], validated_data['currency'])
            
            # Rate limiting
            key = f"payment_attempts:{user_id}"
            attempts = await self.redis_client.incr(key)
            if attempts == 1:
                await self.redis_client.expire(key, 3600)  # 1-hour window
            if attempts > 10:
                raise ValueError("Too many payment attempts. Please try again later.")

            payment = Payment(
                user_id=user_id,
                donation_id=donation_id,
                amount=amount,
                currency=currency,
                status=PaymentStatus.PENDING,
                method=PaymentMethod[payment_method.upper()],
                ip_address=ip_address,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            payment.calculate_fees()
            db.session.add(payment)
            db.session.commit()
            logger.info(f"Payment created: {payment.id} for user {user_id}")
            
            return payment

        except ValidationError as ve:
            logger.error(f"Validation failed: {ve.messages}")
            raise ValueError(f"Validation failed: {ve.messages}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Payment creation failed: {str(e)}", exc_info=True)
            raise

    async def process_payment(self, payment_id, payment_details):
        """Process payment through Stripe"""
        try:
            validated_data = self.payment_details_schema.load(payment_details)
            payment = self._get_payment_or_raise(payment_id)

            intent = await self.stripe_service.create_payment_intent(
                amount=payment.amount,
                currency=payment.currency,
                payment_method_id=validated_data['payment_method_id'],
                metadata={
                    'payment_id': payment_id,
                    'donation_id': payment.donation_id,
                    'user_id': payment.user_id
                }
            )

            payment.status = self.stripe_service.map_stripe_status(intent.status)
            payment.transaction_id = intent.id
            payment.payment_metadata = {
                'stripe_intent_id': intent.id,
                'stripe_client_secret': intent.client_secret,
                'last_payment_error': intent.last_payment_error
            }
            payment.updated_at = datetime.utcnow()
            
            db.session.commit()
            logger.info(f"Payment processed successfully for Payment ID {payment_id}")
            return payment

        except Exception as e:
            db.session.rollback()
            payment.update_status(PaymentStatus.FAILED, str(e))
            db.session.commit()
            logger.error(f"Payment processing failed for Payment ID {payment_id}: {str(e)}", exc_info=True)
            raise e

    async def process_refund(self, payment_id, refund_data=None):
        """Process refund through Stripe"""
        try:
            validated_data = self.refund_schema.load(refund_data) if refund_data else {}
            payment = self._get_payment_or_raise(payment_id)

            if not payment.can_be_refunded():
                raise ValueError("Payment cannot be refunded")

            refund = await self.stripe_service.process_refund(
                payment_intent_id=payment.transaction_id,
                amount=validated_data.get('refund_amount'),
                reason=validated_data.get('reason')
            )

            payment.status = PaymentStatus.REFUNDED
            payment.updated_at = datetime.utcnow()
            payment.payment_metadata = {
                **payment.payment_metadata,
                'refund_id': refund.id,
                'refund_status': refund.status
            }
            
            db.session.commit()
            logger.info(f"Refund successful for Payment ID {payment_id} - Refund ID: {refund.id}")
            return True

        except Exception as e:
            db.session.rollback()
            logger.error(f"Refund failed for Payment ID {payment_id}: {str(e)}", exc_info=True)
            raise e

    def _get_payment_or_raise(self, payment_id):
        """Helper to retrieve a payment or raise an error if not found"""
        payment = Payment.query.get(payment_id)
        if not payment:
            raise ValueError(f"Payment with ID {payment_id} not found.")
        return payment
