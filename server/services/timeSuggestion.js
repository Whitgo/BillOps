const { Activity, TimeEntry, Matter, Client } = require('../models');
const { Op } = require('sequelize');

class TimeSuggestionService {
  // Generate time entry suggestions from activities
  async generateSuggestions(userId) {
    try {
      // Get unprocessed activities
      const activities = await Activity.findAll({
        where: {
          userId,
          isProcessed: false,
        },
        order: [['timestamp', 'DESC']],
      });

      const suggestions = [];

      for (const activity of activities) {
        // Try to match activity to a matter based on keywords
        const suggestedMatter = await this.findMatchingMatter(userId, activity);

        // Generate description
        const description = this.generateDescription(activity);

        // Infer task type
        const taskType = this.inferTaskType(activity);

        // Adjust duration based on activity type and heuristics
        const duration = this.adjustDuration(activity);

        // Create suggested time entry
        const timeEntry = await TimeEntry.create({
          userId,
          activityId: activity.id,
          matterId: suggestedMatter?.id || null,
          date: activity.timestamp,
          duration,
          description,
          taskType,
          status: 'suggested',
          hourlyRate: suggestedMatter?.hourlyRate || 0,
          amount: suggestedMatter ? (duration / 60) * suggestedMatter.hourlyRate : 0,
        });

        // Mark activity as processed
        await activity.update({ isProcessed: true });

        suggestions.push(timeEntry);
      }

      return suggestions;
    } catch (error) {
      console.error('Generate suggestions error:', error);
      throw error;
    }
  }

  // Find matching matter based on keywords
  async findMatchingMatter(userId, activity) {
    try {
      // Get all active matters for user
      const matters = await Matter.findAll({
        where: {
          userId,
          status: 'active',
        },
        include: [{ model: Client, as: 'client' }],
      });

      if (matters.length === 0) return null;

      // Extract keywords from activity
      const keywords = this.extractKeywords(activity);

      // Score each matter
      let bestMatch = null;
      let bestScore = 0;

      for (const matter of matters) {
        let score = 0;

        // Check matter name
        keywords.forEach(keyword => {
          if (matter.name.toLowerCase().includes(keyword)) score += 3;
          if (matter.description?.toLowerCase().includes(keyword)) score += 2;
          if (matter.client.name.toLowerCase().includes(keyword)) score += 3;
          if (matter.client.companyName?.toLowerCase().includes(keyword)) score += 2;
        });

        if (score > bestScore) {
          bestScore = score;
          bestMatch = matter;
        }
      }

      // Return match only if score is significant
      return bestScore >= 2 ? bestMatch : null;
    } catch (error) {
      console.error('Find matching matter error:', error);
      return null;
    }
  }

  // Extract keywords from activity
  extractKeywords(activity) {
    const text = `${activity.subject || ''} ${activity.description || ''}`.toLowerCase();
    const words = text.split(/\s+/);
    
    // Filter out common words and keep meaningful ones
    const stopWords = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'];
    return words.filter(word => word.length > 3 && !stopWords.includes(word));
  }

  // Generate description for time entry
  generateDescription(activity) {
    switch (activity.activityType) {
      case 'email':
        return `Email communication: ${activity.subject}`;
      case 'meeting':
        return `Meeting: ${activity.subject}`;
      case 'document':
        return `Document work: ${activity.subject}`;
      default:
        return activity.description || activity.subject || 'Activity';
    }
  }

  // Infer task type from activity
  inferTaskType(activity) {
    const subject = (activity.subject || '').toLowerCase();
    const description = (activity.description || '').toLowerCase();
    const text = `${subject} ${description}`;

    // Define patterns for common task types
    const patterns = {
      'Research': ['research', 'review', 'analysis', 'investigate'],
      'Communication': ['email', 'call', 'meeting', 'discussion', 'correspondence'],
      'Drafting': ['draft', 'prepare', 'write', 'document', 'memo'],
      'Court': ['court', 'hearing', 'trial', 'filing'],
      'Client Conference': ['client', 'conference', 'consultation'],
      'Administrative': ['admin', 'file', 'organize', 'schedule'],
    };

    for (const [type, keywords] of Object.entries(patterns)) {
      for (const keyword of keywords) {
        if (text.includes(keyword)) {
          return type;
        }
      }
    }

    return 'General';
  }

  // Adjust duration based on heuristics
  // Note: duration is expected to be in minutes
  adjustDuration(activity) {
    let duration = activity.duration || 0;

    // Apply heuristics based on activity type
    switch (activity.activityType) {
      case 'email':
        // Emails: typically 5-30 minutes
        duration = Math.max(5, Math.min(30, duration || 15));
        break;
      case 'meeting':
        // Meetings: use actual duration, round to nearest 15 minutes
        duration = Math.round(duration / 15) * 15;
        break;
      case 'document':
        // Documents: typically 15-60 minutes
        duration = Math.max(15, Math.min(60, duration || 30));
        break;
      default:
        duration = 15;
    }

    return duration;
  }

  // Get suggested time entries for user
  async getSuggestions(userId) {
    try {
      const suggestions = await TimeEntry.findAll({
        where: {
          userId,
          status: 'suggested',
        },
        include: [
          { model: Matter, as: 'matter' },
          { model: Activity, as: 'activity' },
        ],
        order: [['date', 'DESC']],
      });

      return suggestions;
    } catch (error) {
      console.error('Get suggestions error:', error);
      throw error;
    }
  }
}

module.exports = new TimeSuggestionService();
