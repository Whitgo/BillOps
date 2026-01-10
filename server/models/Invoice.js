const { DataTypes } = require('sequelize');
const sequelize = require('../config/sequelize');

const Invoice = sequelize.define('Invoice', {
  id: {
    type: DataTypes.UUID,
    defaultValue: DataTypes.UUIDV4,
    primaryKey: true,
  },
  invoiceNumber: {
    type: DataTypes.STRING,
    unique: true,
    allowNull: false,
  },
  issueDate: {
    type: DataTypes.DATE,
    allowNull: false,
    defaultValue: DataTypes.NOW,
  },
  dueDate: {
    type: DataTypes.DATE,
  },
  status: {
    type: DataTypes.ENUM('draft', 'sent', 'paid', 'overdue', 'cancelled'),
    defaultValue: 'draft',
  },
  subtotal: {
    type: DataTypes.DECIMAL(10, 2),
    defaultValue: 0,
  },
  taxAmount: {
    type: DataTypes.DECIMAL(10, 2),
    defaultValue: 0,
  },
  total: {
    type: DataTypes.DECIMAL(10, 2),
    defaultValue: 0,
  },
  notes: {
    type: DataTypes.TEXT,
  },
  pdfUrl: {
    type: DataTypes.STRING,
  },
}, {
  timestamps: true,
  tableName: 'invoices',
});

module.exports = Invoice;
