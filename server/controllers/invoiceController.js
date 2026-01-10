const { Invoice, Client, TimeEntry, Payment } = require('../models');
const PDFDocument = require('pdfkit');
const fs = require('fs');
const path = require('path');

const invoiceController = {
  // Get all invoices for current user
  getAll: async (req, res) => {
    try {
      const invoices = await Invoice.findAll({
        where: { userId: req.userId },
        include: [
          { model: Client, as: 'client' },
          { model: TimeEntry, as: 'timeEntries' },
          { model: Payment, as: 'payments' },
        ],
        order: [['createdAt', 'DESC']],
      });

      res.json(invoices);
    } catch (error) {
      console.error('Get invoices error:', error);
      res.status(500).json({ error: 'Failed to fetch invoices' });
    }
  },

  // Get single invoice
  getOne: async (req, res) => {
    try {
      const invoice = await Invoice.findOne({
        where: { id: req.params.id, userId: req.userId },
        include: [
          { model: Client, as: 'client' },
          { model: TimeEntry, as: 'timeEntries' },
          { model: Payment, as: 'payments' },
        ],
      });

      if (!invoice) {
        return res.status(404).json({ error: 'Invoice not found' });
      }

      res.json(invoice);
    } catch (error) {
      console.error('Get invoice error:', error);
      res.status(500).json({ error: 'Failed to fetch invoice' });
    }
  },

  // Create invoice
  create: async (req, res) => {
    try {
      const { clientId, timeEntryIds, dueDate, notes } = req.body;

      // Verify client belongs to user
      const client = await Client.findOne({
        where: { id: clientId, userId: req.userId },
      });

      if (!client) {
        return res.status(404).json({ error: 'Client not found' });
      }

      // Fetch time entries
      const timeEntries = await TimeEntry.findAll({
        where: {
          id: timeEntryIds,
          userId: req.userId,
          status: 'approved',
          invoiceId: null,
        },
      });

      if (timeEntries.length === 0) {
        return res.status(400).json({ error: 'No valid time entries found' });
      }

      // Calculate totals
      const subtotal = timeEntries.reduce((sum, entry) => sum + parseFloat(entry.amount), 0);
      const taxAmount = 0; // Add tax calculation if needed
      const total = subtotal + taxAmount;

      // Generate invoice number
      const invoiceCount = await Invoice.count({ where: { userId: req.userId } });
      const invoiceNumber = `INV-${Date.now()}-${invoiceCount + 1}`;

      // Create invoice
      const invoice = await Invoice.create({
        clientId,
        invoiceNumber,
        dueDate,
        notes,
        subtotal,
        taxAmount,
        total,
        userId: req.userId,
      });

      // Update time entries with invoice ID
      await TimeEntry.update(
        { invoiceId: invoice.id, status: 'billed' },
        { where: { id: timeEntryIds } }
      );

      // Fetch complete invoice
      const completeInvoice = await Invoice.findByPk(invoice.id, {
        include: [
          { model: Client, as: 'client' },
          { model: TimeEntry, as: 'timeEntries' },
        ],
      });

      res.status(201).json(completeInvoice);
    } catch (error) {
      console.error('Create invoice error:', error);
      res.status(500).json({ error: 'Failed to create invoice' });
    }
  },

  // Generate PDF
  generatePDF: async (req, res) => {
    try {
      const invoice = await Invoice.findOne({
        where: { id: req.params.id, userId: req.userId },
        include: [
          { model: Client, as: 'client' },
          { model: TimeEntry, as: 'timeEntries' },
        ],
      });

      if (!invoice) {
        return res.status(404).json({ error: 'Invoice not found' });
      }

      // Create PDF
      const doc = new PDFDocument({ margin: 50 });

      // Set response headers
      res.setHeader('Content-Type', 'application/pdf');
      res.setHeader('Content-Disposition', `attachment; filename=invoice-${invoice.invoiceNumber}.pdf`);

      // Pipe PDF to response
      doc.pipe(res);

      // Add content
      doc.fontSize(20).text('INVOICE', { align: 'center' });
      doc.moveDown();

      doc.fontSize(12);
      doc.text(`Invoice Number: ${invoice.invoiceNumber}`);
      doc.text(`Date: ${new Date(invoice.issueDate).toLocaleDateString()}`);
      doc.text(`Due Date: ${invoice.dueDate ? new Date(invoice.dueDate).toLocaleDateString() : 'Upon Receipt'}`);
      doc.moveDown();

      doc.text('Bill To:', { underline: true });
      doc.text(invoice.client.name);
      if (invoice.client.companyName) {
        doc.text(invoice.client.companyName);
      }
      if (invoice.client.address) {
        doc.text(invoice.client.address);
      }
      doc.moveDown();

      // Time entries table
      doc.fontSize(14).text('Time Entries', { underline: true });
      doc.moveDown();

      doc.fontSize(10);
      let y = doc.y;
      doc.text('Date', 50, y);
      doc.text('Description', 120, y);
      doc.text('Duration', 350, y);
      doc.text('Rate', 420, y);
      doc.text('Amount', 490, y);
      
      doc.moveTo(50, y + 15).lineTo(550, y + 15).stroke();
      y += 20;

      invoice.timeEntries.forEach((entry) => {
        const hours = (entry.duration / 60).toFixed(2);
        doc.text(new Date(entry.date).toLocaleDateString(), 50, y);
        doc.text(entry.description.substring(0, 30), 120, y);
        doc.text(`${hours}h`, 350, y);
        doc.text(`$${entry.hourlyRate}`, 420, y);
        doc.text(`$${parseFloat(entry.amount).toFixed(2)}`, 490, y);
        y += 20;
      });

      doc.moveTo(50, y).lineTo(550, y).stroke();
      y += 10;

      // Totals
      doc.fontSize(12);
      doc.text(`Subtotal: $${parseFloat(invoice.subtotal).toFixed(2)}`, 400, y);
      y += 20;
      doc.text(`Tax: $${parseFloat(invoice.taxAmount).toFixed(2)}`, 400, y);
      y += 20;
      doc.fontSize(14).text(`Total: $${parseFloat(invoice.total).toFixed(2)}`, 400, y, { bold: true });

      if (invoice.notes) {
        y += 40;
        doc.fontSize(10).text('Notes:', 50, y);
        doc.text(invoice.notes, 50, y + 15);
      }

      // Finalize PDF
      doc.end();
    } catch (error) {
      console.error('Generate PDF error:', error);
      res.status(500).json({ error: 'Failed to generate PDF' });
    }
  },

  // Update invoice
  update: async (req, res) => {
    try {
      const { status, dueDate, notes } = req.body;

      const invoice = await Invoice.findOne({
        where: { id: req.params.id, userId: req.userId },
      });

      if (!invoice) {
        return res.status(404).json({ error: 'Invoice not found' });
      }

      await invoice.update({
        status: status !== undefined ? status : invoice.status,
        dueDate: dueDate !== undefined ? dueDate : invoice.dueDate,
        notes: notes !== undefined ? notes : invoice.notes,
      });

      res.json(invoice);
    } catch (error) {
      console.error('Update invoice error:', error);
      res.status(500).json({ error: 'Failed to update invoice' });
    }
  },

  // Delete invoice
  delete: async (req, res) => {
    try {
      const invoice = await Invoice.findOne({
        where: { id: req.params.id, userId: req.userId },
      });

      if (!invoice) {
        return res.status(404).json({ error: 'Invoice not found' });
      }

      // Reset time entries
      await TimeEntry.update(
        { invoiceId: null, status: 'approved' },
        { where: { invoiceId: invoice.id } }
      );

      await invoice.destroy();

      res.json({ message: 'Invoice deleted successfully' });
    } catch (error) {
      console.error('Delete invoice error:', error);
      res.status(500).json({ error: 'Failed to delete invoice' });
    }
  },
};

module.exports = invoiceController;
