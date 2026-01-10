const express = require('express');
const router = express.Router();
const clientController = require('../controllers/clientController');
const auth = require('../middleware/auth');

router.use(auth);

router.get('/', clientController.getAll);
router.get('/:id', clientController.getOne);
router.post('/', clientController.create);
router.put('/:id', clientController.update);
router.delete('/:id', clientController.delete);

module.exports = router;
