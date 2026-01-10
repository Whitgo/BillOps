const { Payment, Invoice } = require('../models');
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);

const paymentController = {
  // Get all payments for current user
  getAll: async (req, res) => {
    try {
      const payments = await Payment.findAll({
        include: [
          {
            model: Invoice,
            as: 'invoice',
            where: { userId: req.userId },
          },
        ],
        order: [['createdAt', 'DESC']],
      });

      res.json(payments);
    } catch (error) {
      console.error('Get payments error:', error);
      res.status(500).json({ error: 'Failed to fetch payments' });
    }
  },

  // Create payment intent
  createPaymentIntent: async (req, res) => {
    try {
      const { invoiceId } = req.body;

      const invoice = await Invoice.findOne({
        where: { id: invoiceId, userId: req.userId },
        include: [{ model: Payment, as: 'payments' }],
      });

      if (!invoice) {
        return res.status(404).json({ error: 'Invoice not found' });
      }

      // Check if invoice is already paid
      if (invoice.status === 'paid') {
        return res.status(400).json({ error: 'Invoice is already paid' });
      }

      // Create Stripe payment intent
      const paymentIntent = await stripe.paymentIntents.create({
        amount: Math.round(parseFloat(invoice.total) * 100), // Convert to cents
        currency: 'usd',
        metadata: {
          invoiceId: invoice.id,
          invoiceNumber: invoice.invoiceNumber,
        },
      });

      // Create payment record
      const payment = await Payment.create({
        invoiceId: invoice.id,
        amount: invoice.total,
        paymentMethod: 'credit_card',
        status: 'pending',
        stripePaymentIntentId: paymentIntent.id,
      });

      res.json({
        clientSecret: paymentIntent.client_secret,
        paymentId: payment.id,
      });
    } catch (error) {
      console.error('Create payment intent error:', error);
      res.status(500).json({ error: 'Failed to create payment intent' });
    }
  },

  // Stripe webhook handler
  webhook: async (req, res) => {
    const sig = req.headers['stripe-signature'];
    let event;

    try {
      event = stripe.webhooks.constructEvent(
        req.body,
        sig,
        process.env.STRIPE_WEBHOOK_SECRET
      );
    } catch (err) {
      console.error('Webhook signature verification failed:', err.message);
      return res.status(400).send(`Webhook Error: ${err.message}`);
    }

    // Handle the event
    switch (event.type) {
      case 'payment_intent.succeeded':
        const paymentIntent = event.data.object;
        
        // Update payment status
        const payment = await Payment.findOne({
          where: { stripePaymentIntentId: paymentIntent.id },
        });

        if (payment) {
          await payment.update({
            status: 'completed',
            paymentDate: new Date(),
            transactionId: paymentIntent.id,
          });

          // Update invoice status
          const invoice = await Invoice.findByPk(payment.invoiceId);
          if (invoice) {
            await invoice.update({ status: 'paid' });
          }
        }
        break;

      case 'payment_intent.payment_failed':
        const failedPaymentIntent = event.data.object;
        
        const failedPayment = await Payment.findOne({
          where: { stripePaymentIntentId: failedPaymentIntent.id },
        });

        if (failedPayment) {
          await failedPayment.update({ status: 'failed' });
        }
        break;

      default:
        console.log(`Unhandled event type ${event.type}`);
    }

    res.json({ received: true });
  },

  // Get payment details
  getOne: async (req, res) => {
    try {
      const payment = await Payment.findOne({
        where: { id: req.params.id },
        include: [
          {
            model: Invoice,
            as: 'invoice',
            where: { userId: req.userId },
          },
        ],
      });

      if (!payment) {
        return res.status(404).json({ error: 'Payment not found' });
      }

      res.json(payment);
    } catch (error) {
      console.error('Get payment error:', error);
      res.status(500).json({ error: 'Failed to fetch payment' });
    }
  },
};

module.exports = paymentController;
