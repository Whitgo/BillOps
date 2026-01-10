const express = require('express');
const router = express.Router();
const auth = require('../middleware/auth');
const emailTracking = require('../services/emailTracking');
const calendarTracking = require('../services/calendarTracking');
const documentTracking = require('../services/documentTracking');
const timeSuggestion = require('../services/timeSuggestion');
const { triggerUserSync } = require('../services/backgroundJobs');

// Get auth URLs for integrations
router.get('/gmail/auth-url', auth, (req, res) => {
  const url = emailTracking.getAuthUrl(req.userId);
  res.json({ url });
});

router.get('/calendar/auth-url', auth, (req, res) => {
  const url = calendarTracking.getAuthUrl(req.userId);
  res.json({ url });
});

router.get('/drive/auth-url', auth, (req, res) => {
  const url = documentTracking.getAuthUrl(req.userId);
  res.json({ url });
});

// OAuth callbacks (to be called from frontend after user authorization)
router.post('/gmail/callback', auth, async (req, res) => {
  try {
    const { code } = req.body;
    const { tokens } = await emailTracking.oauth2Client.getToken(code);
    await emailTracking.saveTokens(req.userId, tokens);
    res.json({ success: true });
  } catch (error) {
    console.error('Gmail callback error:', error);
    res.status(500).json({ error: 'Failed to connect Gmail' });
  }
});

router.post('/calendar/callback', auth, async (req, res) => {
  try {
    const { code } = req.body;
    const { tokens } = await calendarTracking.oauth2Client.getToken(code);
    await calendarTracking.saveTokens(req.userId, tokens);
    res.json({ success: true });
  } catch (error) {
    console.error('Calendar callback error:', error);
    res.status(500).json({ error: 'Failed to connect Calendar' });
  }
});

router.post('/drive/callback', auth, async (req, res) => {
  try {
    const { code } = req.body;
    const { tokens } = await documentTracking.oauth2Client.getToken(code);
    await documentTracking.saveTokens(req.userId, tokens);
    res.json({ success: true });
  } catch (error) {
    console.error('Drive callback error:', error);
    res.status(500).json({ error: 'Failed to connect Drive' });
  }
});

// Trigger manual sync
router.post('/sync', auth, async (req, res) => {
  try {
    await triggerUserSync(req.userId);
    res.json({ message: 'Sync started' });
  } catch (error) {
    console.error('Sync trigger error:', error);
    res.status(500).json({ error: 'Failed to trigger sync' });
  }
});

// Get time entry suggestions
router.get('/suggestions', auth, async (req, res) => {
  try {
    const suggestions = await timeSuggestion.getSuggestions(req.userId);
    res.json(suggestions);
  } catch (error) {
    console.error('Get suggestions error:', error);
    res.status(500).json({ error: 'Failed to fetch suggestions' });
  }
});

module.exports = router;
