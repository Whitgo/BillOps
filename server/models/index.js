const sequelize = require('../config/sequelize');
const User = require('./User');
const Client = require('./Client');
const Matter = require('./Matter');
const Activity = require('./Activity');
const TimeEntry = require('./TimeEntry');
const Invoice = require('./Invoice');
const Payment = require('./Payment');

// Define associations

// User associations
User.hasMany(Client, { foreignKey: 'userId', as: 'clients' });
User.hasMany(Matter, { foreignKey: 'userId', as: 'matters' });
User.hasMany(Activity, { foreignKey: 'userId', as: 'activities' });
User.hasMany(TimeEntry, { foreignKey: 'userId', as: 'timeEntries' });
User.hasMany(Invoice, { foreignKey: 'userId', as: 'invoices' });

// Client associations
Client.belongsTo(User, { foreignKey: 'userId', as: 'user' });
Client.hasMany(Matter, { foreignKey: 'clientId', as: 'matters' });
Client.hasMany(Invoice, { foreignKey: 'clientId', as: 'invoices' });

// Matter associations
Matter.belongsTo(User, { foreignKey: 'userId', as: 'user' });
Matter.belongsTo(Client, { foreignKey: 'clientId', as: 'client' });
Matter.hasMany(TimeEntry, { foreignKey: 'matterId', as: 'timeEntries' });

// Activity associations
Activity.belongsTo(User, { foreignKey: 'userId', as: 'user' });
Activity.hasOne(TimeEntry, { foreignKey: 'activityId', as: 'timeEntry' });

// TimeEntry associations
TimeEntry.belongsTo(User, { foreignKey: 'userId', as: 'user' });
TimeEntry.belongsTo(Matter, { foreignKey: 'matterId', as: 'matter' });
TimeEntry.belongsTo(Activity, { foreignKey: 'activityId', as: 'activity' });
TimeEntry.belongsTo(Invoice, { foreignKey: 'invoiceId', as: 'invoice' });

// Invoice associations
Invoice.belongsTo(User, { foreignKey: 'userId', as: 'user' });
Invoice.belongsTo(Client, { foreignKey: 'clientId', as: 'client' });
Invoice.hasMany(TimeEntry, { foreignKey: 'invoiceId', as: 'timeEntries' });
Invoice.hasMany(Payment, { foreignKey: 'invoiceId', as: 'payments' });

// Payment associations
Payment.belongsTo(Invoice, { foreignKey: 'invoiceId', as: 'invoice' });

module.exports = {
  sequelize,
  User,
  Client,
  Matter,
  Activity,
  TimeEntry,
  Invoice,
  Payment,
};
