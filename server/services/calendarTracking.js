const { google } = require('googleapis');
const { Activity, User } = require('../models');
const { encrypt, decrypt } = require('../utils/encryption');

class CalendarTrackingService {
  constructor() {
    this.oauth2Client = new google.auth.OAuth2(
      process.env.GOOGLE_CALENDAR_CLIENT_ID,
      process.env.GOOGLE_CALENDAR_CLIENT_SECRET,
      `${process.env.FRONTEND_URL}/auth/calendar/callback`
    );
  }

  // Get authorization URL
  getAuthUrl(userId) {
    return this.oauth2Client.generateAuthUrl({
      access_type: 'offline',
      scope: ['https://www.googleapis.com/auth/calendar.readonly'],
      state: userId,
    });
  }

  // Save tokens
  async saveTokens(userId, tokens) {
    const user = await User.findByPk(userId);
    if (!user) throw new Error('User not found');

    await user.update({
      googleCalendarAccessToken: encrypt(tokens.access_token),
      googleCalendarRefreshToken: tokens.refresh_token ? encrypt(tokens.refresh_token) : user.googleCalendarRefreshToken,
    });
  }

  // Get user's Calendar client
  async getCalendarClient(userId) {
    const user = await User.findByPk(userId);
    if (!user || !user.googleCalendarAccessToken) {
      throw new Error('Calendar not connected');
    }

    this.oauth2Client.setCredentials({
      access_token: decrypt(user.googleCalendarAccessToken),
      refresh_token: user.googleCalendarRefreshToken ? decrypt(user.googleCalendarRefreshToken) : null,
    });

    return google.calendar({ version: 'v3', auth: this.oauth2Client });
  }

  // Sync calendar events
  async syncCalendarEvents(userId) {
    try {
      const calendar = await this.getCalendarClient(userId);

      // Get events from last 7 days
      const sevenDaysAgo = new Date();
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

      const response = await calendar.events.list({
        calendarId: 'primary',
        timeMin: sevenDaysAgo.toISOString(),
        timeMax: new Date().toISOString(),
        maxResults: 100,
        singleEvents: true,
        orderBy: 'startTime',
      });

      if (!response.data.items) {
        return [];
      }

      const activities = [];

      for (const event of response.data.items) {
        // Skip if no start time or all-day events
        if (!event.start?.dateTime) continue;

        // Check if already processed
        const existing = await Activity.findOne({
          where: { sourceId: event.id, userId },
        });

        if (existing) continue;

        // Calculate duration
        const start = new Date(event.start.dateTime);
        const end = new Date(event.end.dateTime);
        const duration = Math.round((end - start) / (1000 * 60)); // minutes

        // Create activity
        const activity = await Activity.create({
          userId,
          activityType: 'meeting',
          timestamp: start,
          duration,
          subject: event.summary || 'No Title',
          description: event.description || `Meeting: ${event.summary}`,
          sourceId: event.id,
          metadata: {
            attendees: event.attendees?.map(a => a.email) || [],
            location: event.location || '',
            eventId: event.id,
          },
        });

        activities.push(activity);
      }

      return activities;
    } catch (error) {
      console.error('Calendar sync error:', error);
      throw error;
    }
  }
}

module.exports = new CalendarTrackingService();
