# BillOps - Automated Billing & Time Capture

A comprehensive web application for law firms and professionals to automatically track time, manage clients and matters, generate invoices, and process payments.

## Features

### Core Functionality

1. **Passive Time Tracking**
   - Connects to Gmail, Google Calendar, and Google Drive
   - Automatically detects and logs emails, meetings, and document edits
   - Captures metadata including timestamps, durations, and descriptions

2. **AI-Suggested Time Entries**
   - Transforms captured activities into time entry suggestions
   - Uses heuristics to infer duration, task type, and descriptions
   - Automatically matches activities to clients and matters using keyword analysis
   - User-friendly review interface to approve, edit, or reject suggestions

3. **Client & Matter Management**
   - Full CRUD operations for clients and matters
   - Support for hourly billing rates
   - Track multiple matters per client
   - Matter status tracking (active, closed, pending)

4. **Invoice Generation**
   - Professional PDF invoice generation
   - Aggregates approved time entries by client and matter
   - Includes line items, rates, totals, and firm details
   - Download or email invoices

5. **Payment Integration**
   - Stripe integration for online payments
   - Support for credit card and ACH payments
   - Automatic invoice status updates upon payment
   - Payment tracking and history

## Technology Stack

### Backend
- **Node.js** with Express.js
- **PostgreSQL** database with Sequelize ORM
- **Bull** for background job processing
- **Redis** for job queue management
- **Google APIs** for Gmail, Calendar, and Drive integration
- **Stripe** for payment processing
- **PDFKit** for PDF generation
- **JWT** for authentication
- **bcrypt** for password hashing
- **crypto-js** for data encryption

### Frontend
- **React** 18
- **React Router** for navigation
- **Axios** for API requests
- **Stripe Elements** for payment forms

## Setup Instructions

### Prerequisites

- Node.js (v16 or higher)
- PostgreSQL (v12 or higher)
- Redis (v6 or higher)
- Stripe account
- Google Cloud Platform account with enabled APIs

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Whitgo/BillOps.git
   cd BillOps
   ```

2. **Install dependencies**
   ```bash
   npm run install-all
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and configure database, JWT secret, Google OAuth credentials, Stripe keys, and encryption key.

4. **Set up PostgreSQL database**
   ```bash
   createdb billops
   ```

5. **Start Redis**
   ```bash
   redis-server
   ```

6. **Run the application**
   ```bash
   # Terminal 1 - Backend
   npm run server
   
   # Terminal 2 - Frontend
   npm run client
   ```

Server runs on http://localhost:3001  
Client runs on http://localhost:3000

## API Documentation

See full API documentation in the README for endpoints including:
- Authentication (register, login)
- Clients (CRUD operations)
- Matters (CRUD operations)
- Time Entries (CRUD, approve/reject suggestions)
- Invoices (CRUD, PDF generation)
- Payments (Stripe integration)
- Integrations (Gmail, Calendar, Drive OAuth)

## Database Schema

**Main Tables:**
- Users (authentication, OAuth tokens)
- Clients (customer information)
- Matters (client projects with hourly rates)
- Activities (captured emails, meetings, documents)
- TimeEntries (billable time with suggestions)
- Invoices (billing documents)
- Payments (Stripe transactions)

## License

See LICENSE file for details.
