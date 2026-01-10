const { Client, Matter } = require('../models');

const clientController = {
  // Get all clients for current user
  getAll: async (req, res) => {
    try {
      const clients = await Client.findAll({
        where: { userId: req.userId },
        include: [{ model: Matter, as: 'matters' }],
        order: [['createdAt', 'DESC']],
      });

      res.json(clients);
    } catch (error) {
      console.error('Get clients error:', error);
      res.status(500).json({ error: 'Failed to fetch clients' });
    }
  },

  // Get single client
  getOne: async (req, res) => {
    try {
      const client = await Client.findOne({
        where: { id: req.params.id, userId: req.userId },
        include: [{ model: Matter, as: 'matters' }],
      });

      if (!client) {
        return res.status(404).json({ error: 'Client not found' });
      }

      res.json(client);
    } catch (error) {
      console.error('Get client error:', error);
      res.status(500).json({ error: 'Failed to fetch client' });
    }
  },

  // Create client
  create: async (req, res) => {
    try {
      const { name, email, phone, address, companyName, notes } = req.body;

      const client = await Client.create({
        name,
        email,
        phone,
        address,
        companyName,
        notes,
        userId: req.userId,
      });

      res.status(201).json(client);
    } catch (error) {
      console.error('Create client error:', error);
      res.status(500).json({ error: 'Failed to create client' });
    }
  },

  // Update client
  update: async (req, res) => {
    try {
      const { name, email, phone, address, companyName, notes, isActive } = req.body;

      const client = await Client.findOne({
        where: { id: req.params.id, userId: req.userId },
      });

      if (!client) {
        return res.status(404).json({ error: 'Client not found' });
      }

      await client.update({
        name: name !== undefined ? name : client.name,
        email: email !== undefined ? email : client.email,
        phone: phone !== undefined ? phone : client.phone,
        address: address !== undefined ? address : client.address,
        companyName: companyName !== undefined ? companyName : client.companyName,
        notes: notes !== undefined ? notes : client.notes,
        isActive: isActive !== undefined ? isActive : client.isActive,
      });

      res.json(client);
    } catch (error) {
      console.error('Update client error:', error);
      res.status(500).json({ error: 'Failed to update client' });
    }
  },

  // Delete client
  delete: async (req, res) => {
    try {
      const client = await Client.findOne({
        where: { id: req.params.id, userId: req.userId },
      });

      if (!client) {
        return res.status(404).json({ error: 'Client not found' });
      }

      await client.destroy();

      res.json({ message: 'Client deleted successfully' });
    } catch (error) {
      console.error('Delete client error:', error);
      res.status(500).json({ error: 'Failed to delete client' });
    }
  },
};

module.exports = clientController;
