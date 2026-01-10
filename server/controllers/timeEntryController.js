const { TimeEntry, Matter, Activity } = require('../models');

const timeEntryController = {
  // Get all time entries for current user
  getAll: async (req, res) => {
    try {
      const { status, matterId } = req.query;
      const where = { userId: req.userId };

      if (status) {
        where.status = status;
      }
      if (matterId) {
        where.matterId = matterId;
      }

      const timeEntries = await TimeEntry.findAll({
        where,
        include: [
          { model: Matter, as: 'matter' },
          { model: Activity, as: 'activity' },
        ],
        order: [['date', 'DESC']],
      });

      res.json(timeEntries);
    } catch (error) {
      console.error('Get time entries error:', error);
      res.status(500).json({ error: 'Failed to fetch time entries' });
    }
  },

  // Get single time entry
  getOne: async (req, res) => {
    try {
      const timeEntry = await TimeEntry.findOne({
        where: { id: req.params.id, userId: req.userId },
        include: [
          { model: Matter, as: 'matter' },
          { model: Activity, as: 'activity' },
        ],
      });

      if (!timeEntry) {
        return res.status(404).json({ error: 'Time entry not found' });
      }

      res.json(timeEntry);
    } catch (error) {
      console.error('Get time entry error:', error);
      res.status(500).json({ error: 'Failed to fetch time entry' });
    }
  },

  // Create time entry
  create: async (req, res) => {
    try {
      const { matterId, date, duration, description, taskType, isBillable, notes } = req.body;

      // Verify matter belongs to user
      const matter = await Matter.findOne({
        where: { id: matterId, userId: req.userId },
      });

      if (!matter) {
        return res.status(404).json({ error: 'Matter not found' });
      }

      // Calculate amount
      const hourlyRate = matter.hourlyRate;
      const amount = (duration / 60) * hourlyRate;

      const timeEntry = await TimeEntry.create({
        matterId,
        date,
        duration,
        description,
        taskType,
        isBillable,
        notes,
        hourlyRate,
        amount,
        status: 'approved',
        userId: req.userId,
      });

      res.status(201).json(timeEntry);
    } catch (error) {
      console.error('Create time entry error:', error);
      res.status(500).json({ error: 'Failed to create time entry' });
    }
  },

  // Update time entry
  update: async (req, res) => {
    try {
      const { date, duration, description, taskType, status, isBillable, notes } = req.body;

      const timeEntry = await TimeEntry.findOne({
        where: { id: req.params.id, userId: req.userId },
        include: [{ model: Matter, as: 'matter' }],
      });

      if (!timeEntry) {
        return res.status(404).json({ error: 'Time entry not found' });
      }

      // Recalculate amount if duration changed
      let amount = timeEntry.amount;
      if (duration !== undefined && duration !== timeEntry.duration) {
        amount = (duration / 60) * timeEntry.hourlyRate;
      }

      await timeEntry.update({
        date: date !== undefined ? date : timeEntry.date,
        duration: duration !== undefined ? duration : timeEntry.duration,
        description: description !== undefined ? description : timeEntry.description,
        taskType: taskType !== undefined ? taskType : timeEntry.taskType,
        status: status !== undefined ? status : timeEntry.status,
        isBillable: isBillable !== undefined ? isBillable : timeEntry.isBillable,
        notes: notes !== undefined ? notes : timeEntry.notes,
        amount,
      });

      res.json(timeEntry);
    } catch (error) {
      console.error('Update time entry error:', error);
      res.status(500).json({ error: 'Failed to update time entry' });
    }
  },

  // Approve time entry
  approve: async (req, res) => {
    try {
      const timeEntry = await TimeEntry.findOne({
        where: { id: req.params.id, userId: req.userId },
      });

      if (!timeEntry) {
        return res.status(404).json({ error: 'Time entry not found' });
      }

      await timeEntry.update({ status: 'approved' });

      res.json(timeEntry);
    } catch (error) {
      console.error('Approve time entry error:', error);
      res.status(500).json({ error: 'Failed to approve time entry' });
    }
  },

  // Reject time entry
  reject: async (req, res) => {
    try {
      const timeEntry = await TimeEntry.findOne({
        where: { id: req.params.id, userId: req.userId },
      });

      if (!timeEntry) {
        return res.status(404).json({ error: 'Time entry not found' });
      }

      await timeEntry.update({ status: 'rejected' });

      res.json(timeEntry);
    } catch (error) {
      console.error('Reject time entry error:', error);
      res.status(500).json({ error: 'Failed to reject time entry' });
    }
  },

  // Delete time entry
  delete: async (req, res) => {
    try {
      const timeEntry = await TimeEntry.findOne({
        where: { id: req.params.id, userId: req.userId },
      });

      if (!timeEntry) {
        return res.status(404).json({ error: 'Time entry not found' });
      }

      await timeEntry.destroy();

      res.json({ message: 'Time entry deleted successfully' });
    } catch (error) {
      console.error('Delete time entry error:', error);
      res.status(500).json({ error: 'Failed to delete time entry' });
    }
  },
};

module.exports = timeEntryController;
