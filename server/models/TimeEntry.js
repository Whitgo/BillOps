const { DataTypes } = require('sequelize');
const sequelize = require('../config/sequelize');

const TimeEntry = sequelize.define('TimeEntry', {
  id: {
    type: DataTypes.UUID,
    defaultValue: DataTypes.UUIDV4,
    primaryKey: true,
  },
  date: {
    type: DataTypes.DATE,
    allowNull: false,
  },
  duration: {
    type: DataTypes.INTEGER, // Duration in minutes
    allowNull: false,
  },
  description: {
    type: DataTypes.TEXT,
    allowNull: false,
  },
  taskType: {
    type: DataTypes.STRING,
  },
  status: {
    type: DataTypes.ENUM('suggested', 'approved', 'rejected', 'billed'),
    defaultValue: 'suggested',
  },
  hourlyRate: {
    type: DataTypes.DECIMAL(10, 2),
  },
  amount: {
    type: DataTypes.DECIMAL(10, 2),
  },
  isBillable: {
    type: DataTypes.BOOLEAN,
    defaultValue: true,
  },
  notes: {
    type: DataTypes.TEXT,
  },
}, {
  timestamps: true,
  tableName: 'time_entries',
});

module.exports = TimeEntry;
