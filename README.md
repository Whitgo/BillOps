# BillOps
Automated Billing & Time Capture for Law Firms

BillOps is a comprehensive billing and time tracking system designed for law firms. It automatically captures billable hours from emails, calendar events, and document activity, generates professional PDF invoices, and integrates with Stripe for online payments.

## Features

### 1. Client & Matter Management
- Create and manage clients with contact information
- Set up legal matters with custom hourly rates
- Organize time entries and invoices by client and matter
- Track matter status (active, closed, on hold)

### 2. Passive Time Tracking
Automatically capture billable time from multiple sources:
- **Email Activity**: Track time spent on email communications
- **Calendar Events**: Convert meetings and appointments to billable hours
- **Document Activity**: Monitor document creation, editing, and review time

### 3. Time Entry Management
- Create manual time entries
- Review and approve automatically captured time
- Edit time descriptions and hours
- Track entry status (pending, approved, invoiced)

### 4. Invoice Generation
- Create professional PDF invoices from approved time entries
- Clean, itemized invoice format
- Automatic calculation of totals
- Track invoice status (draft, sent, paid, overdue)

### 5. Online Payments
- Stripe integration for credit card payments
- ACH bank transfer support
- Secure payment processing
- Automatic invoice status updates on payment

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/Whitgo/BillOps.git
cd BillOps
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables (optional):
```bash
export STRIPE_SECRET_KEY="your_stripe_secret_key"
export STRIPE_WEBHOOK_SECRET="your_stripe_webhook_secret"
export DATABASE_URL="sqlite:///billops.db"  # Or your database URL
```

5. Run the application:
```bash
python app.py
```

6. Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

### Getting Started

1. **Add Clients**: Navigate to the Clients tab and add your first client with name, email, phone, and address.

2. **Create Matters**: In the Matters tab, create legal matters for your clients. Set the hourly rate for each matter.

3. **Track Time**: You can track time in two ways:
   - **Manual Entry**: Go to Time Entries tab and manually add time entries
   - **Passive Tracking**: Use the Time Tracking tab to capture time from emails, calendar events, or document activity

4. **Approve Time**: Review pending time entries and approve them for billing.

5. **Generate Invoices**: In the Invoices tab, select a client, choose approved time entries, and create an invoice. Download the PDF to send to your client.

6. **Accept Payments**: Set up Stripe to accept online payments via credit card or ACH transfer.

### API Endpoints

BillOps provides a RESTful API for integration with other systems:

#### Clients
- `GET /api/clients` - List all clients
- `POST /api/clients` - Create a new client
- `GET /api/clients/{id}` - Get client details
- `PUT /api/clients/{id}` - Update client
- `DELETE /api/clients/{id}` - Delete client

#### Matters
- `GET /api/matters` - List all matters
- `POST /api/matters` - Create a new matter
- `GET /api/matters/{id}` - Get matter details
- `PUT /api/matters/{id}` - Update matter
- `DELETE /api/matters/{id}` - Delete matter

#### Time Entries
- `GET /api/time-entries` - List all time entries
- `POST /api/time-entries` - Create a time entry
- `GET /api/time-entries/{id}` - Get time entry details
- `PUT /api/time-entries/{id}` - Update time entry
- `POST /api/time-entries/{id}/approve` - Approve time entry
- `DELETE /api/time-entries/{id}` - Delete time entry

#### Time Tracking
- `POST /api/time-tracking/capture-email` - Capture time from email
- `POST /api/time-tracking/capture-calendar` - Capture time from calendar
- `POST /api/time-tracking/capture-document` - Capture time from document

#### Invoices
- `GET /api/invoices` - List all invoices
- `POST /api/invoices` - Create a new invoice
- `GET /api/invoices/{id}` - Get invoice details
- `GET /api/invoices/{id}/pdf` - Download invoice PDF
- `POST /api/invoices/{id}/send` - Mark invoice as sent
- `PUT /api/invoices/{id}` - Update invoice
- `DELETE /api/invoices/{id}` - Delete invoice

#### Payments
- `POST /api/payments/create-intent` - Create Stripe payment intent
- `POST /api/payments/webhook` - Stripe webhook handler
- `POST /api/payments/ach-setup` - Set up ACH payment

## Configuration

### Environment Variables

- `DATABASE_URL`: Database connection string (default: `sqlite:///billops.db`)
- `STRIPE_SECRET_KEY`: Your Stripe secret API key
- `STRIPE_WEBHOOK_SECRET`: Your Stripe webhook signing secret

### Stripe Setup

1. Create a Stripe account at https://stripe.com
2. Get your API keys from the Stripe Dashboard
3. Set up a webhook endpoint pointing to `https://yourdomain.com/api/payments/webhook`
4. Add the webhook secret to your environment variables

## Development

### Project Structure

```
BillOps/
├── app.py                    # Main Flask application
├── models.py                 # Database models
├── time_tracker.py          # Time tracking logic
├── invoice_generator.py     # PDF invoice generation
├── payment_integration.py   # Stripe payment processing
├── requirements.txt         # Python dependencies
├── static/
│   └── index.html          # Web interface
├── invoices/               # Generated invoice PDFs (created at runtime)
└── README.md
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest
```

## Security Considerations

- Always use environment variables for sensitive data (API keys, database credentials)
- Use HTTPS in production
- Set up proper authentication and authorization for the API
- Regularly update dependencies
- Back up your database regularly

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or contributions, please open an issue on GitHub.
