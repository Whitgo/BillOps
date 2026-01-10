const express = require('express');
const router = express.Router();
const timeEntryController = require('../controllers/timeEntryController');
const auth = require('../middleware/auth');

router.use(auth);

router.get('/', timeEntryController.getAll);
router.get('/:id', timeEntryController.getOne);
router.post('/', timeEntryController.create);
router.put('/:id', timeEntryController.update);
router.post('/:id/approve', timeEntryController.approve);
router.post('/:id/reject', timeEntryController.reject);
router.delete('/:id', timeEntryController.delete);

module.exports = router;
