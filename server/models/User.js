const { DataTypes } = require('sequelize');
const sequelize = require('../config/sequelize');
const bcrypt = require('bcrypt');

const User = sequelize.define('User', {
  id: {
    type: DataTypes.UUID,
    defaultValue: DataTypes.UUIDV4,
    primaryKey: true,
  },
  email: {
    type: DataTypes.STRING,
    allowNull: false,
    unique: true,
    validate: {
      isEmail: true,
    },
  },
  password: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  firstName: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  lastName: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  firmName: {
    type: DataTypes.STRING,
  },
  role: {
    type: DataTypes.ENUM('admin', 'lawyer', 'staff'),
    defaultValue: 'lawyer',
  },
  isActive: {
    type: DataTypes.BOOLEAN,
    defaultValue: true,
  },
  gmailAccessToken: {
    type: DataTypes.TEXT,
  },
  gmailRefreshToken: {
    type: DataTypes.TEXT,
  },
  outlookAccessToken: {
    type: DataTypes.TEXT,
  },
  outlookRefreshToken: {
    type: DataTypes.TEXT,
  },
  googleCalendarAccessToken: {
    type: DataTypes.TEXT,
  },
  googleCalendarRefreshToken: {
    type: DataTypes.TEXT,
  },
  googleDriveAccessToken: {
    type: DataTypes.TEXT,
  },
  googleDriveRefreshToken: {
    type: DataTypes.TEXT,
  },
}, {
  timestamps: true,
  tableName: 'users',
  hooks: {
    beforeCreate: async (user) => {
      if (user.password) {
        const salt = await bcrypt.genSalt(10);
        user.password = await bcrypt.hash(user.password, salt);
      }
    },
    beforeUpdate: async (user) => {
      if (user.changed('password')) {
        const salt = await bcrypt.genSalt(10);
        user.password = await bcrypt.hash(user.password, salt);
      }
    },
  },
});

User.prototype.comparePassword = async function(candidatePassword) {
  return bcrypt.compare(candidatePassword, this.password);
};

module.exports = User;
