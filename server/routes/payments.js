const express = require('express');
const router = express.Router();
const paymentController = require('../controllers/paymentController');
const auth = require('../middleware/auth');
const { paymentLimiter } = require('../middleware/rateLimiter');

router.post('/create-payment-intent', auth, paymentLimiter, paymentController.createPaymentIntent);
router.post('/webhook', express.raw({ type: 'application/json' }), paymentController.webhook);
router.get('/', auth, paymentController.getAll);
router.get('/:id', auth, paymentController.getOne);

module.exports = router;
