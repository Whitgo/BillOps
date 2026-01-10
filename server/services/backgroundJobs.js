const Queue = require('bull');
const emailTracking = require('./emailTracking');
const calendarTracking = require('./calendarTracking');
const documentTracking = require('./documentTracking');
const timeSuggestion = require('./timeSuggestion');
const { User } = require('../models');

// Create queues
const syncQueue = new Queue('activity-sync', {
  redis: {
    host: process.env.REDIS_HOST || 'localhost',
    port: process.env.REDIS_PORT || 6379,
  },
});

// Process sync jobs
syncQueue.process('sync-user-activities', async (job) => {
  const { userId } = job.data;
  
  try {
    console.log(`Syncing activities for user ${userId}`);

    const results = {
      emails: [],
      meetings: [],
      documents: [],
      suggestions: [],
    };

    // Sync emails
    try {
      results.emails = await emailTracking.syncSentEmails(userId);
      console.log(`Synced ${results.emails.length} emails`);
    } catch (error) {
      console.error('Email sync failed:', error.message);
    }

    // Sync calendar
    try {
      results.meetings = await calendarTracking.syncCalendarEvents(userId);
      console.log(`Synced ${results.meetings.length} meetings`);
    } catch (error) {
      console.error('Calendar sync failed:', error.message);
    }

    // Sync documents
    try {
      results.documents = await documentTracking.syncDocumentEdits(userId);
      console.log(`Synced ${results.documents.length} documents`);
    } catch (error) {
      console.error('Document sync failed:', error.message);
    }

    // Generate suggestions
    try {
      results.suggestions = await timeSuggestion.generateSuggestions(userId);
      console.log(`Generated ${results.suggestions.length} suggestions`);
    } catch (error) {
      console.error('Suggestion generation failed:', error.message);
    }

    return results;
  } catch (error) {
    console.error('Sync job failed:', error);
    throw error;
  }
});

// Schedule periodic sync for all active users
const schedulePeriodicSync = () => {
  // Run every hour
  syncQueue.add(
    'sync-all-users',
    {},
    {
      repeat: { cron: '0 * * * *' }, // Every hour
      removeOnComplete: true,
      removeOnFail: false,
    }
  );
};

// Process periodic sync for all users
syncQueue.process('sync-all-users', async (job) => {
  try {
    const users = await User.findAll({
      where: { isActive: true },
    });

    for (const user of users) {
      // Add individual sync job for each user
      await syncQueue.add(
        'sync-user-activities',
        { userId: user.id },
        {
          removeOnComplete: true,
          removeOnFail: false,
        }
      );
    }

    return { usersQueued: users.length };
  } catch (error) {
    console.error('Periodic sync failed:', error);
    throw error;
  }
});

// Manual trigger for specific user
const triggerUserSync = async (userId) => {
  return syncQueue.add(
    'sync-user-activities',
    { userId },
    {
      removeOnComplete: true,
      removeOnFail: false,
    }
  );
};

module.exports = {
  syncQueue,
  schedulePeriodicSync,
  triggerUserSync,
};
