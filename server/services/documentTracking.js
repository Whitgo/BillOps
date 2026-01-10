const { google } = require('googleapis');
const { Activity, User } = require('../models');
const { encrypt, decrypt } = require('../utils/encryption');

class DocumentTrackingService {
  constructor() {
    this.oauth2Client = new google.auth.OAuth2(
      process.env.GOOGLE_DRIVE_CLIENT_ID,
      process.env.GOOGLE_DRIVE_CLIENT_SECRET,
      `${process.env.FRONTEND_URL}/auth/drive/callback`
    );
  }

  // Get authorization URL
  getAuthUrl(userId) {
    return this.oauth2Client.generateAuthUrl({
      access_type: 'offline',
      scope: ['https://www.googleapis.com/auth/drive.readonly'],
      state: userId,
    });
  }

  // Save tokens
  async saveTokens(userId, tokens) {
    const user = await User.findByPk(userId);
    if (!user) throw new Error('User not found');

    await user.update({
      googleDriveAccessToken: encrypt(tokens.access_token),
      googleDriveRefreshToken: tokens.refresh_token ? encrypt(tokens.refresh_token) : user.googleDriveRefreshToken,
    });
  }

  // Get user's Drive client
  async getDriveClient(userId) {
    const user = await User.findByPk(userId);
    if (!user || !user.googleDriveAccessToken) {
      throw new Error('Drive not connected');
    }

    this.oauth2Client.setCredentials({
      access_token: decrypt(user.googleDriveAccessToken),
      refresh_token: user.googleDriveRefreshToken ? decrypt(user.googleDriveRefreshToken) : null,
    });

    return google.drive({ version: 'v3', auth: this.oauth2Client });
  }

  // Sync document edits
  async syncDocumentEdits(userId) {
    try {
      const drive = await this.getDriveClient(userId);

      // Get files modified in last 7 days
      const sevenDaysAgo = new Date();
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
      const query = `modifiedTime > '${sevenDaysAgo.toISOString()}' and trashed = false`;

      const response = await drive.files.list({
        q: query,
        fields: 'files(id, name, modifiedTime, mimeType, owners)',
        pageSize: 100,
        orderBy: 'modifiedTime desc',
      });

      if (!response.data.files) {
        return [];
      }

      const activities = [];

      for (const file of response.data.files) {
        // Only track documents, spreadsheets, and presentations
        const trackableTypes = [
          'application/vnd.google-apps.document',
          'application/vnd.google-apps.spreadsheet',
          'application/vnd.google-apps.presentation',
          'application/pdf',
          'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        ];

        if (!trackableTypes.includes(file.mimeType)) continue;

        // Check if already processed (use file ID + modified time as unique key)
        const sourceId = `${file.id}-${file.modifiedTime}`;
        const existing = await Activity.findOne({
          where: { sourceId, userId },
        });

        if (existing) continue;

        // Create activity
        const activity = await Activity.create({
          userId,
          activityType: 'document',
          timestamp: new Date(file.modifiedTime),
          duration: 30, // Default 30 minutes for document edits
          subject: file.name,
          description: `Document edited: ${file.name}`,
          sourceId,
          metadata: {
            fileId: file.id,
            fileName: file.name,
            mimeType: file.mimeType,
          },
        });

        activities.push(activity);
      }

      return activities;
    } catch (error) {
      console.error('Document sync error:', error);
      throw error;
    }
  }
}

module.exports = new DocumentTrackingService();
