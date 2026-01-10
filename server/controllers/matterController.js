const { Matter, Client, TimeEntry } = require('../models');

const matterController = {
  // Get all matters for current user
  getAll: async (req, res) => {
    try {
      const matters = await Matter.findAll({
        where: { userId: req.userId },
        include: [
          { model: Client, as: 'client' },
          { model: TimeEntry, as: 'timeEntries' },
        ],
        order: [['createdAt', 'DESC']],
      });

      res.json(matters);
    } catch (error) {
      console.error('Get matters error:', error);
      res.status(500).json({ error: 'Failed to fetch matters' });
    }
  },

  // Get single matter
  getOne: async (req, res) => {
    try {
      const matter = await Matter.findOne({
        where: { id: req.params.id, userId: req.userId },
        include: [
          { model: Client, as: 'client' },
          { model: TimeEntry, as: 'timeEntries' },
        ],
      });

      if (!matter) {
        return res.status(404).json({ error: 'Matter not found' });
      }

      res.json(matter);
    } catch (error) {
      console.error('Get matter error:', error);
      res.status(500).json({ error: 'Failed to fetch matter' });
    }
  },

  // Create matter
  create: async (req, res) => {
    try {
      const { clientId, name, description, matterNumber, hourlyRate, startDate, endDate } = req.body;

      // Verify client belongs to user
      const client = await Client.findOne({
        where: { id: clientId, userId: req.userId },
      });

      if (!client) {
        return res.status(404).json({ error: 'Client not found' });
      }

      const matter = await Matter.create({
        clientId,
        name,
        description,
        matterNumber,
        hourlyRate,
        startDate,
        endDate,
        userId: req.userId,
      });

      res.status(201).json(matter);
    } catch (error) {
      console.error('Create matter error:', error);
      res.status(500).json({ error: 'Failed to create matter' });
    }
  },

  // Update matter
  update: async (req, res) => {
    try {
      const { name, description, matterNumber, hourlyRate, startDate, endDate, status } = req.body;

      const matter = await Matter.findOne({
        where: { id: req.params.id, userId: req.userId },
      });

      if (!matter) {
        return res.status(404).json({ error: 'Matter not found' });
      }

      await matter.update({
        name: name !== undefined ? name : matter.name,
        description: description !== undefined ? description : matter.description,
        matterNumber: matterNumber !== undefined ? matterNumber : matter.matterNumber,
        hourlyRate: hourlyRate !== undefined ? hourlyRate : matter.hourlyRate,
        startDate: startDate !== undefined ? startDate : matter.startDate,
        endDate: endDate !== undefined ? endDate : matter.endDate,
        status: status !== undefined ? status : matter.status,
      });

      res.json(matter);
    } catch (error) {
      console.error('Update matter error:', error);
      res.status(500).json({ error: 'Failed to update matter' });
    }
  },

  // Delete matter
  delete: async (req, res) => {
    try {
      const matter = await Matter.findOne({
        where: { id: req.params.id, userId: req.userId },
      });

      if (!matter) {
        return res.status(404).json({ error: 'Matter not found' });
      }

      await matter.destroy();

      res.json({ message: 'Matter deleted successfully' });
    } catch (error) {
      console.error('Delete matter error:', error);
      res.status(500).json({ error: 'Failed to delete matter' });
    }
  },
};

module.exports = matterController;
