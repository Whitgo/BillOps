const { google } = require('googleapis');
const { Activity, User } = require('../models');
const { encrypt, decrypt } = require('../utils/encryption');

class EmailTrackingService {
  constructor() {
    this.oauth2Client = new google.auth.OAuth2(
      process.env.GMAIL_CLIENT_ID,
      process.env.GMAIL_CLIENT_SECRET,
      `${process.env.FRONTEND_URL}/auth/gmail/callback`
    );
  }

  // Get authorization URL
  getAuthUrl(userId) {
    return this.oauth2Client.generateAuthUrl({
      access_type: 'offline',
      scope: ['https://www.googleapis.com/auth/gmail.readonly'],
      state: userId,
    });
  }

  // Save tokens
  async saveTokens(userId, tokens) {
    const user = await User.findByPk(userId);
    if (!user) throw new Error('User not found');

    await user.update({
      gmailAccessToken: encrypt(tokens.access_token),
      gmailRefreshToken: tokens.refresh_token ? encrypt(tokens.refresh_token) : user.gmailRefreshToken,
    });
  }

  // Get user's Gmail client
  async getGmailClient(userId) {
    const user = await User.findByPk(userId);
    if (!user || !user.gmailAccessToken) {
      throw new Error('Gmail not connected');
    }

    this.oauth2Client.setCredentials({
      access_token: decrypt(user.gmailAccessToken),
      refresh_token: user.gmailRefreshToken ? decrypt(user.gmailRefreshToken) : null,
    });

    return google.gmail({ version: 'v1', auth: this.oauth2Client });
  }

  // Sync sent emails
  async syncSentEmails(userId) {
    try {
      const gmail = await this.getGmailClient(userId);

      // Get sent emails from last 7 days
      const sevenDaysAgo = new Date();
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
      const query = `in:sent after:${Math.floor(sevenDaysAgo.getTime() / 1000)}`;

      const response = await gmail.users.messages.list({
        userId: 'me',
        q: query,
        maxResults: 100,
      });

      if (!response.data.messages) {
        return [];
      }

      const activities = [];

      for (const message of response.data.messages) {
        // Check if already processed
        const existing = await Activity.findOne({
          where: { sourceId: message.id, userId },
        });

        if (existing) continue;

        // Get message details
        const details = await gmail.users.messages.get({
          userId: 'me',
          id: message.id,
        });

        const headers = details.data.payload.headers;
        const subject = headers.find(h => h.name === 'Subject')?.value || 'No Subject';
        const to = headers.find(h => h.name === 'To')?.value || '';
        const date = headers.find(h => h.name === 'Date')?.value;

        // Create activity
        const activity = await Activity.create({
          userId,
          activityType: 'email',
          timestamp: new Date(date),
          duration: 15, // Default 15 minutes for emails
          subject,
          description: `Email sent to ${to}`,
          sourceId: message.id,
          metadata: {
            to,
            messageId: message.id,
          },
        });

        activities.push(activity);
      }

      return activities;
    } catch (error) {
      console.error('Email sync error:', error);
      throw error;
    }
  }
}

module.exports = new EmailTrackingService();
