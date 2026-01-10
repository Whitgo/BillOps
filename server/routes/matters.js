const express = require('express');
const router = express.Router();
const matterController = require('../controllers/matterController');
const auth = require('../middleware/auth');

router.use(auth);

router.get('/', matterController.getAll);
router.get('/:id', matterController.getOne);
router.post('/', matterController.create);
router.put('/:id', matterController.update);
router.delete('/:id', matterController.delete);

module.exports = router;
