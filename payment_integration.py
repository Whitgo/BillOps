"""Payment integration module for Stripe and ACH"""
import os
import stripe


class PaymentProcessor:
    """Handles payment processing with Stripe for credit cards and ACH"""
    
    def __init__(self, stripe_secret_key=None):
        """
        Initialize the payment processor
        
        Args:
            stripe_secret_key: Stripe API secret key
        """
        self.stripe_secret_key = stripe_secret_key or os.environ.get('STRIPE_SECRET_KEY', '')
        if self.stripe_secret_key:
            stripe.api_key = self.stripe_secret_key
        self.webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
    
    def create_payment_intent(self, amount, currency='usd', metadata=None):
        """
        Create a Stripe Payment Intent for credit card payments
        
        Args:
            amount: Amount to charge (in dollars)
            currency: Currency code (default: 'usd')
            metadata: Dictionary of metadata to attach to the payment
        
        Returns:
            Payment Intent object
        """
        if not self.stripe_secret_key:
            raise Exception("Stripe API key not configured")
        
        # Convert amount to cents
        amount_cents = int(amount * 100)
        
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                metadata=metadata or {},
                automatic_payment_methods={'enabled': True},
            )
            return {
                'id': intent.id,
                'client_secret': intent.client_secret,
                'amount': amount,
                'currency': currency,
                'status': intent.status
            }
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
    
    def setup_ach_payment(self, amount, customer_name, customer_email, metadata=None):
        """
        Set up ACH bank transfer payment
        
        Args:
            amount: Amount to charge
            customer_name: Name of the customer
            customer_email: Email of the customer
            metadata: Dictionary of metadata to attach
        
        Returns:
            Setup information for ACH payment
        """
        if not self.stripe_secret_key:
            raise Exception("Stripe API key not configured")
        
        try:
            # Create a customer
            customer = stripe.Customer.create(
                name=customer_name,
                email=customer_email,
                metadata=metadata or {}
            )
            
            # Create a setup intent for ACH
            setup_intent = stripe.SetupIntent.create(
                customer=customer.id,
                payment_method_types=['us_bank_account'],
                metadata=metadata or {}
            )
            
            return {
                'customer_id': customer.id,
                'setup_intent_id': setup_intent.id,
                'client_secret': setup_intent.client_secret,
                'amount': amount,
                'status': setup_intent.status
            }
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
    
    def charge_ach(self, customer_id, payment_method_id, amount, metadata=None):
        """
        Charge a customer via ACH using a verified payment method
        
        Args:
            customer_id: Stripe customer ID
            payment_method_id: ID of the verified payment method
            amount: Amount to charge (in dollars)
            metadata: Dictionary of metadata
        
        Returns:
            Payment Intent object
        """
        if not self.stripe_secret_key:
            raise Exception("Stripe API key not configured")
        
        amount_cents = int(amount * 100)
        
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency='usd',
                customer=customer_id,
                payment_method=payment_method_id,
                payment_method_types=['us_bank_account'],
                confirm=True,
                metadata=metadata or {}
            )
            return {
                'id': intent.id,
                'amount': amount,
                'status': intent.status,
                'payment_method': payment_method_id
            }
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
    
    def verify_webhook(self, payload, signature_header):
        """
        Verify and parse a Stripe webhook event
        
        Args:
            payload: Raw webhook payload
            signature_header: Stripe-Signature header value
        
        Returns:
            Parsed webhook event
        """
        if not self.webhook_secret:
            raise Exception("Webhook secret not configured")
        
        try:
            event = stripe.Webhook.construct_event(
                payload, signature_header, self.webhook_secret
            )
            return event
        except ValueError:
            raise Exception("Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise Exception("Invalid signature")
    
    def get_payment_status(self, payment_intent_id):
        """
        Get the status of a payment intent
        
        Args:
            payment_intent_id: ID of the payment intent
        
        Returns:
            Payment status information
        """
        if not self.stripe_secret_key:
            raise Exception("Stripe API key not configured")
        
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return {
                'id': intent.id,
                'status': intent.status,
                'amount': intent.amount / 100,
                'currency': intent.currency,
                'payment_method': intent.payment_method
            }
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
    
    def create_refund(self, payment_intent_id, amount=None):
        """
        Create a refund for a payment
        
        Args:
            payment_intent_id: ID of the payment intent to refund
            amount: Amount to refund (in dollars). If None, refunds the full amount
        
        Returns:
            Refund object
        """
        if not self.stripe_secret_key:
            raise Exception("Stripe API key not configured")
        
        try:
            refund_params = {'payment_intent': payment_intent_id}
            if amount is not None:
                refund_params['amount'] = int(amount * 100)
            
            refund = stripe.Refund.create(**refund_params)
            return {
                'id': refund.id,
                'status': refund.status,
                'amount': refund.amount / 100,
                'payment_intent': payment_intent_id
            }
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
