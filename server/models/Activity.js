const { DataTypes } = require('sequelize');
const sequelize = require('../config/sequelize');

const Activity = sequelize.define('Activity', {
  id: {
    type: DataTypes.UUID,
    defaultValue: DataTypes.UUIDV4,
    primaryKey: true,
  },
  activityType: {
    type: DataTypes.ENUM('email', 'meeting', 'document'),
    allowNull: false,
  },
  timestamp: {
    type: DataTypes.DATE,
    allowNull: false,
  },
  duration: {
    type: DataTypes.INTEGER, // Duration in minutes
  },
  subject: {
    type: DataTypes.STRING,
  },
  description: {
    type: DataTypes.TEXT,
  },
  metadata: {
    type: DataTypes.JSONB,
    defaultValue: {},
  },
  sourceId: {
    type: DataTypes.STRING, // External ID from email/calendar/drive
  },
  isProcessed: {
    type: DataTypes.BOOLEAN,
    defaultValue: false,
  },
}, {
  timestamps: true,
  tableName: 'activities',
});

module.exports = Activity;
