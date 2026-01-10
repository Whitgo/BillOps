const { DataTypes } = require('sequelize');
const sequelize = require('../config/sequelize');

const Matter = sequelize.define('Matter', {
  id: {
    type: DataTypes.UUID,
    defaultValue: DataTypes.UUIDV4,
    primaryKey: true,
  },
  name: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  description: {
    type: DataTypes.TEXT,
  },
  matterNumber: {
    type: DataTypes.STRING,
    unique: true,
  },
  status: {
    type: DataTypes.ENUM('active', 'closed', 'pending'),
    defaultValue: 'active',
  },
  hourlyRate: {
    type: DataTypes.DECIMAL(10, 2),
    allowNull: false,
  },
  startDate: {
    type: DataTypes.DATE,
  },
  endDate: {
    type: DataTypes.DATE,
  },
}, {
  timestamps: true,
  tableName: 'matters',
});

module.exports = Matter;
