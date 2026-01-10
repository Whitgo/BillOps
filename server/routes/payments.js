const express = require('express');
const router = express.Router();
const paymentController = require('../controllers/paymentController');
const auth = require('../middleware/auth');

router.post('/create-payment-intent', auth, paymentController.createPaymentIntent);
router.post('/webhook', express.raw({ type: 'application/json' }), paymentController.webhook);
router.get('/', auth, paymentController.getAll);
router.get('/:id', auth, paymentController.getOne);

module.exports = router;
