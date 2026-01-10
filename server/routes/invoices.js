const express = require('express');
const router = express.Router();
const invoiceController = require('../controllers/invoiceController');
const auth = require('../middleware/auth');

router.use(auth);

router.get('/', invoiceController.getAll);
router.get('/:id', invoiceController.getOne);
router.post('/', invoiceController.create);
router.put('/:id', invoiceController.update);
router.get('/:id/pdf', invoiceController.generatePDF);
router.delete('/:id', invoiceController.delete);

module.exports = router;
