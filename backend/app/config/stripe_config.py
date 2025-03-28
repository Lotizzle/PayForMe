import os
import logging

logger = logging.getLogger(__name__)

class StripeConfig:
    SECRET_KEY: str = os.getenv('STRIPE_SECRET_KEY')
    WEBHOOK_SECRET: str = os.getenv('STRIPE_WEBHOOK_SECRET')
    PAYMENT_RETURN_URL: str = os.getenv('STRIPE_PAYMENT_RETURN_URL')
    WEBHOOK_TOLERANCE: int = int(os.getenv('STRIPE_WEBHOOK_TOLERANCE', 300))
    SUPPORTED_CURRENCIES = {'USD', 'EUR', 'GBP', 'CAD', 'AUD'}
    PLATFORM_FEE_PERCENT = 0.05  # 5% platform fee
    STRIPE_FEE_PERCENT = 0.029
    STRIPE_FEE_FIXED = 0.30
    MINIMUM_AMOUNT = {
        'USD': 0.50,
        'EUR': 0.50,
        'GBP': 0.30,
        'CAD': 0.50,
        'AUD': 0.50
    }

    # Rate limit settings
    RATE_LIMIT_ATTEMPTS: int = int(os.getenv('RATE_LIMIT_ATTEMPTS', 10))  # Default to 10 attempts
    RATE_LIMIT_WINDOW: int = int(os.getenv('RATE_LIMIT_WINDOW', 3600))    # Default to 1 hour in seconds
    MAX_METADATA_LENGTH = 500  # Stripe's limit per metadata field
    MAX_RETRIES = 3
    RATE_LIMIT_PERIOD = 10  # seconds
    RATE_LIMIT_COUNT = 5
    # Check required configurations
    @classmethod
    def validate_config(cls):
        if not cls.SECRET_KEY:
            logger.error("Stripe secret key is not configured.")
            raise EnvironmentError("Stripe secret key not configured.")
        if not cls.WEBHOOK_SECRET:
            logger.error("Stripe webhook secret is not configured.")
            raise EnvironmentError("Stripe webhook secret not configured.")

StripeConfig.validate_config()
