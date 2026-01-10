# BillOps Setup Guide

This guide will walk you through setting up BillOps from scratch.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** (v16 or higher)
  - Download from https://nodejs.org/
  - Verify: `node --version`

- **PostgreSQL** (v12 or higher)
  - macOS: `brew install postgresql`
  - Ubuntu: `sudo apt-get install postgresql`
  - Windows: Download from https://www.postgresql.org/download/
  - Verify: `psql --version`

- **Redis** (v6 or higher)
  - macOS: `brew install redis`
  - Ubuntu: `sudo apt-get install redis-server`
  - Windows: Use WSL or Docker
  - Verify: `redis-cli --version`

## Step 1: Clone and Install

```bash
# Clone the repository
git clone https://github.com/Whitgo/BillOps.git
cd BillOps

# Install all dependencies (both server and client)
npm run install-all
```

## Step 2: Database Setup

### Create PostgreSQL Database

```bash
# Connect to PostgreSQL
psql postgres

# Create database
CREATE DATABASE billops;

# Create user (optional)
CREATE USER billops_user WITH PASSWORD 'your_password';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE billops TO billops_user;

# Exit
\q
```

### Verify Database Connection

```bash
psql -d billops
```

## Step 3: Environment Configuration

### Copy Environment Template

```bash
cp .env.example .env
```

### Edit .env File

Open `.env` in your text editor and configure:

#### Database Configuration
```env
DATABASE_URL=postgresql://billops_user:your_password@localhost:5432/billops
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=billops
DATABASE_USER=billops_user
DATABASE_PASSWORD=your_password
```

#### Server Configuration
```env
PORT=3001
NODE_ENV=development
```

#### JWT Configuration
```env
JWT_SECRET=your-very-secure-random-string-min-32-chars
JWT_EXPIRES_IN=7d
```

Generate a secure JWT secret:
```bash
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

#### Encryption Key
```env
ENCRYPTION_KEY=your-32-character-encryption-key-here
```

Generate encryption key:
```bash
node -e "console.log(require('crypto').randomBytes(16).toString('hex'))"
```

## Step 4: Google Cloud Setup

### Create Google Cloud Project

1. Go to https://console.cloud.google.com/
2. Click "Select a project" → "New Project"
3. Name: "BillOps"
4. Click "Create"

### Enable Required APIs

1. Navigate to "APIs & Services" → "Library"
2. Enable these APIs:
   - Gmail API
   - Google Calendar API
   - Google Drive API

### Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Configure OAuth consent screen:
   - User Type: External
   - App name: BillOps
   - User support email: your email
   - Developer contact: your email
   - Add scopes:
     - Gmail: `https://www.googleapis.com/auth/gmail.readonly`
     - Calendar: `https://www.googleapis.com/auth/calendar.readonly`
     - Drive: `https://www.googleapis.com/auth/drive.readonly`
4. Create OAuth Client ID:
   - Application type: Web application
   - Name: BillOps Web Client
   - Authorized redirect URIs:
     ```
     http://localhost:3000/auth/gmail/callback
     http://localhost:3000/auth/calendar/callback
     http://localhost:3000/auth/drive/callback
     ```
5. Copy Client ID and Client Secret

### Add to .env

```env
GMAIL_CLIENT_ID=your-gmail-client-id
GMAIL_CLIENT_SECRET=your-gmail-client-secret

GOOGLE_CALENDAR_CLIENT_ID=your-calendar-client-id
GOOGLE_CALENDAR_CLIENT_SECRET=your-calendar-client-secret

GOOGLE_DRIVE_CLIENT_ID=your-drive-client-id
GOOGLE_DRIVE_CLIENT_SECRET=your-drive-client-secret
```

Note: You can use the same OAuth client for all three services.

## Step 5: Stripe Setup

### Create Stripe Account

1. Go to https://stripe.com/
2. Sign up for an account
3. Complete account verification

### Get API Keys

1. Go to Dashboard → Developers → API keys
2. Copy "Publishable key" and "Secret key"
3. Use test keys for development

### Add to .env

```env
STRIPE_SECRET_KEY=sk_test_your_secret_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key
```

### Set Up Webhook (Optional for Development)

1. Install Stripe CLI: https://stripe.com/docs/stripe-cli
2. Run: `stripe login`
3. Forward webhooks:
   ```bash
   stripe listen --forward-to localhost:3001/api/payments/webhook
   ```
4. Copy webhook signing secret to `.env`:
   ```env
   STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
   ```

## Step 6: Start Services

### Terminal 1: Start Redis

```bash
redis-server
```

Keep this terminal open.

### Terminal 2: Start Backend Server

```bash
npm run server
```

You should see:
```
Database connection established successfully.
Database synchronized.
Background jobs scheduled.
Server is running on port 3001
```

### Terminal 3: Start Frontend

```bash
npm run client
```

The React app will start and open in your browser at http://localhost:3000

## Step 7: Test the Application

### Register a User

1. Go to http://localhost:3000/register
2. Fill in the form:
   - First Name: John
   - Last Name: Doe
   - Email: john@example.com
   - Password: password123
   - Firm Name: Doe Law Firm
3. Click "Register"

### Create a Client

1. Navigate to "Clients"
2. Click "Add Client"
3. Fill in client details
4. Click "Save"

### Create a Matter

1. Navigate to "Matters"
2. Click "Add Matter"
3. Select client
4. Fill in matter details (including hourly rate)
5. Click "Save"

### Connect Integrations

1. Navigate to "Integrations"
2. Click "Connect Gmail"
3. Sign in with Google account
4. Grant permissions
5. Repeat for Calendar and Drive

### Sync Activities

1. On Integrations page, click "Sync Now"
2. Wait a few moments
3. Navigate to "Time Entries"
4. Review suggested time entries
5. Approve or reject suggestions

### Create an Invoice

1. Ensure you have approved time entries
2. Navigate to "Invoices"
3. (Feature to be added in UI - use API for now)

## Troubleshooting

### Database Connection Error

**Error:** `Connection refused to localhost:5432`

**Solution:**
1. Check PostgreSQL is running: `pg_isready`
2. Start PostgreSQL:
   - macOS: `brew services start postgresql`
   - Ubuntu: `sudo service postgresql start`

### Redis Connection Error

**Error:** `Error connecting to Redis`

**Solution:**
1. Check Redis is running: `redis-cli ping`
2. Should return: `PONG`
3. Start Redis: `redis-server`

### Port Already in Use

**Error:** `Port 3001 is already in use`

**Solution:**
1. Find process: `lsof -i :3001`
2. Kill process: `kill -9 <PID>`
3. Or change PORT in `.env`

### Google OAuth Error

**Error:** `redirect_uri_mismatch`

**Solution:**
1. Check redirect URI in Google Cloud Console
2. Must exactly match: `http://localhost:3000/auth/gmail/callback`
3. No trailing slash
4. Correct protocol (http/https)

### Stripe Webhook Error

**Error:** `Webhook signature verification failed`

**Solution:**
1. Ensure webhook secret is correct in `.env`
2. Use Stripe CLI for local testing:
   ```bash
   stripe listen --forward-to localhost:3001/api/payments/webhook
   ```

## Development Tips

### Reset Database

```bash
# Drop and recreate database
psql postgres -c "DROP DATABASE billops;"
psql postgres -c "CREATE DATABASE billops;"

# Restart server to recreate tables
npm run server
```

### View Logs

Backend logs appear in the terminal where you ran `npm run server`.

### Clear Redis Queue

```bash
redis-cli FLUSHALL
```

### Hot Reload

- Backend: Uses nodemon, automatically restarts on file changes
- Frontend: Create React App, hot reloads automatically

## Production Deployment

See separate DEPLOYMENT.md guide for production setup instructions.

## Getting Help

- Check README.md for general information
- Check API.md for API documentation
- Open an issue on GitHub
- Contact support

## Next Steps

- Explore the UI
- Test all features
- Set up production environment
- Customize for your needs
- Invite team members
