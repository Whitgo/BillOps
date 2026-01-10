"""Main Flask application for BillOps"""
import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_file
from models import db, Client, Matter, TimeEntry, Invoice
from invoice_generator import generate_invoice_pdf
from time_tracker import TimeTracker
from payment_integration import PaymentProcessor

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///billops.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['STRIPE_SECRET_KEY'] = os.environ.get('STRIPE_SECRET_KEY', '')

db.init_app(app)

# Initialize services
time_tracker = TimeTracker()
payment_processor = PaymentProcessor(app.config['STRIPE_SECRET_KEY'])

# Initialize database on startup
with app.app_context():
    db.create_all()


# Client endpoints
@app.route('/api/clients', methods=['GET'])
def get_clients():
    """Get all clients"""
    clients = Client.query.all()
    return jsonify([client.to_dict() for client in clients])


@app.route('/api/clients/<int:client_id>', methods=['GET'])
def get_client(client_id):
    """Get a specific client"""
    client = Client.query.get_or_404(client_id)
    return jsonify(client.to_dict())


@app.route('/api/clients', methods=['POST'])
def create_client():
    """Create a new client"""
    data = request.json
    client = Client(
        name=data['name'],
        email=data.get('email'),
        phone=data.get('phone'),
        address=data.get('address')
    )
    db.session.add(client)
    db.session.commit()
    return jsonify(client.to_dict()), 201


@app.route('/api/clients/<int:client_id>', methods=['PUT'])
def update_client(client_id):
    """Update a client"""
    client = Client.query.get_or_404(client_id)
    data = request.json
    
    client.name = data.get('name', client.name)
    client.email = data.get('email', client.email)
    client.phone = data.get('phone', client.phone)
    client.address = data.get('address', client.address)
    
    db.session.commit()
    return jsonify(client.to_dict())


@app.route('/api/clients/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    """Delete a client"""
    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()
    return '', 204


# Matter endpoints
@app.route('/api/matters', methods=['GET'])
def get_matters():
    """Get all matters"""
    client_id = request.args.get('client_id', type=int)
    if client_id:
        matters = Matter.query.filter_by(client_id=client_id).all()
    else:
        matters = Matter.query.all()
    return jsonify([matter.to_dict() for matter in matters])


@app.route('/api/matters/<int:matter_id>', methods=['GET'])
def get_matter(matter_id):
    """Get a specific matter"""
    matter = Matter.query.get_or_404(matter_id)
    return jsonify(matter.to_dict())


@app.route('/api/matters', methods=['POST'])
def create_matter():
    """Create a new matter"""
    data = request.json
    
    # Generate matter number if not provided
    matter_number = data.get('matter_number')
    if not matter_number:
        count = Matter.query.count() + 1
        matter_number = f"M{count:05d}"
    
    matter = Matter(
        client_id=data['client_id'],
        name=data['name'],
        description=data.get('description'),
        matter_number=matter_number,
        status=data.get('status', 'active'),
        hourly_rate=data.get('hourly_rate', 250.0)
    )
    db.session.add(matter)
    db.session.commit()
    return jsonify(matter.to_dict()), 201


@app.route('/api/matters/<int:matter_id>', methods=['PUT'])
def update_matter(matter_id):
    """Update a matter"""
    matter = Matter.query.get_or_404(matter_id)
    data = request.json
    
    matter.name = data.get('name', matter.name)
    matter.description = data.get('description', matter.description)
    matter.status = data.get('status', matter.status)
    matter.hourly_rate = data.get('hourly_rate', matter.hourly_rate)
    
    db.session.commit()
    return jsonify(matter.to_dict())


@app.route('/api/matters/<int:matter_id>', methods=['DELETE'])
def delete_matter(matter_id):
    """Delete a matter"""
    matter = Matter.query.get_or_404(matter_id)
    db.session.delete(matter)
    db.session.commit()
    return '', 204


# Time Entry endpoints
@app.route('/api/time-entries', methods=['GET'])
def get_time_entries():
    """Get all time entries"""
    matter_id = request.args.get('matter_id', type=int)
    status = request.args.get('status')
    
    query = TimeEntry.query
    if matter_id:
        query = query.filter_by(matter_id=matter_id)
    if status:
        query = query.filter_by(status=status)
    
    time_entries = query.order_by(TimeEntry.date.desc()).all()
    return jsonify([entry.to_dict() for entry in time_entries])


@app.route('/api/time-entries/<int:entry_id>', methods=['GET'])
def get_time_entry(entry_id):
    """Get a specific time entry"""
    entry = TimeEntry.query.get_or_404(entry_id)
    return jsonify(entry.to_dict())


@app.route('/api/time-entries', methods=['POST'])
def create_time_entry():
    """Create a new time entry"""
    data = request.json
    
    matter = Matter.query.get_or_404(data['matter_id'])
    
    # Parse date
    entry_date = datetime.strptime(data['date'], '%Y-%m-%d').date() if 'date' in data else datetime.utcnow().date()
    
    entry = TimeEntry(
        matter_id=data['matter_id'],
        description=data['description'],
        hours=data['hours'],
        date=entry_date,
        source=data.get('source', 'manual'),
        source_reference=data.get('source_reference'),
        rate=data.get('rate', matter.hourly_rate),
        status=data.get('status', 'pending')
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify(entry.to_dict()), 201


@app.route('/api/time-entries/<int:entry_id>', methods=['PUT'])
def update_time_entry(entry_id):
    """Update a time entry"""
    entry = TimeEntry.query.get_or_404(entry_id)
    data = request.json
    
    if 'description' in data:
        entry.description = data['description']
    if 'hours' in data:
        entry.hours = data['hours']
    if 'date' in data:
        entry.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    if 'status' in data:
        entry.status = data['status']
    if 'rate' in data:
        entry.rate = data['rate']
    
    db.session.commit()
    return jsonify(entry.to_dict())


@app.route('/api/time-entries/<int:entry_id>', methods=['DELETE'])
def delete_time_entry(entry_id):
    """Delete a time entry"""
    entry = TimeEntry.query.get_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    return '', 204


@app.route('/api/time-entries/<int:entry_id>/approve', methods=['POST'])
def approve_time_entry(entry_id):
    """Approve a time entry"""
    entry = TimeEntry.query.get_or_404(entry_id)
    entry.status = 'approved'
    db.session.commit()
    return jsonify(entry.to_dict())


# Time Tracking endpoints
@app.route('/api/time-tracking/capture-email', methods=['POST'])
def capture_email_time():
    """Capture time from email activity"""
    data = request.json
    result = time_tracker.capture_from_email(
        email_subject=data['subject'],
        email_body=data.get('body', ''),
        email_from=data.get('from'),
        email_to=data.get('to'),
        timestamp=data.get('timestamp'),
        duration_minutes=data.get('duration_minutes')
    )
    return jsonify(result)


@app.route('/api/time-tracking/capture-calendar', methods=['POST'])
def capture_calendar_time():
    """Capture time from calendar events"""
    data = request.json
    result = time_tracker.capture_from_calendar(
        event_title=data['title'],
        event_description=data.get('description', ''),
        start_time=data['start_time'],
        end_time=data['end_time'],
        attendees=data.get('attendees', [])
    )
    return jsonify(result)


@app.route('/api/time-tracking/capture-document', methods=['POST'])
def capture_document_time():
    """Capture time from document activity"""
    data = request.json
    result = time_tracker.capture_from_document(
        document_name=data['name'],
        document_type=data.get('type'),
        activity_type=data['activity_type'],
        duration_minutes=data.get('duration_minutes'),
        timestamp=data.get('timestamp')
    )
    return jsonify(result)


# Invoice endpoints
@app.route('/api/invoices', methods=['GET'])
def get_invoices():
    """Get all invoices"""
    client_id = request.args.get('client_id', type=int)
    status = request.args.get('status')
    
    query = Invoice.query
    if client_id:
        query = query.filter_by(client_id=client_id)
    if status:
        query = query.filter_by(status=status)
    
    invoices = query.order_by(Invoice.created_at.desc()).all()
    return jsonify([invoice.to_dict() for invoice in invoices])


@app.route('/api/invoices/<int:invoice_id>', methods=['GET'])
def get_invoice(invoice_id):
    """Get a specific invoice"""
    invoice = Invoice.query.get_or_404(invoice_id)
    return jsonify(invoice.to_dict())


@app.route('/api/invoices', methods=['POST'])
def create_invoice():
    """Create a new invoice from approved time entries"""
    data = request.json
    
    client_id = data['client_id']
    matter_id = data.get('matter_id')
    time_entry_ids = data.get('time_entry_ids', [])
    
    # Generate invoice number
    count = Invoice.query.count() + 1
    invoice_number = f"INV-{count:05d}"
    
    # Calculate due date (30 days from issue date)
    issue_date = datetime.strptime(data['issue_date'], '%Y-%m-%d').date() if 'issue_date' in data else datetime.utcnow().date()
    due_date = issue_date + timedelta(days=30)
    
    # Calculate total from time entries
    total_amount = 0.0
    if time_entry_ids:
        entries = TimeEntry.query.filter(TimeEntry.id.in_(time_entry_ids)).all()
        for entry in entries:
            if entry.status == 'approved':
                total_amount += entry.hours * entry.rate
    
    invoice = Invoice(
        invoice_number=invoice_number,
        client_id=client_id,
        matter_id=matter_id,
        status='draft',
        total_amount=total_amount,
        issue_date=issue_date,
        due_date=due_date,
        notes=data.get('notes')
    )
    db.session.add(invoice)
    db.session.flush()
    
    # Update time entries to link to this invoice
    if time_entry_ids:
        for entry in entries:
            entry.invoice_id = invoice.id
            entry.status = 'invoiced'
    
    db.session.commit()
    return jsonify(invoice.to_dict()), 201


@app.route('/api/invoices/<int:invoice_id>', methods=['PUT'])
def update_invoice(invoice_id):
    """Update an invoice"""
    invoice = Invoice.query.get_or_404(invoice_id)
    data = request.json
    
    if 'status' in data:
        invoice.status = data['status']
    if 'notes' in data:
        invoice.notes = data['notes']
    if 'due_date' in data:
        invoice.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
    
    db.session.commit()
    return jsonify(invoice.to_dict())


@app.route('/api/invoices/<int:invoice_id>', methods=['DELETE'])
def delete_invoice(invoice_id):
    """Delete an invoice"""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Unlink time entries
    for entry in invoice.time_entries:
        entry.invoice_id = None
        entry.status = 'approved'
    
    db.session.delete(invoice)
    db.session.commit()
    return '', 204


@app.route('/api/invoices/<int:invoice_id>/pdf', methods=['GET'])
def download_invoice_pdf(invoice_id):
    """Generate and download invoice PDF"""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Get time entries for this invoice
    time_entries = TimeEntry.query.filter_by(invoice_id=invoice_id).all()
    
    pdf_path = generate_invoice_pdf(invoice, time_entries)
    return send_file(pdf_path, as_attachment=True, download_name=f"{invoice.invoice_number}.pdf")


@app.route('/api/invoices/<int:invoice_id>/send', methods=['POST'])
def send_invoice(invoice_id):
    """Mark invoice as sent"""
    invoice = Invoice.query.get_or_404(invoice_id)
    invoice.status = 'sent'
    db.session.commit()
    return jsonify(invoice.to_dict())


# Payment endpoints
@app.route('/api/payments/create-intent', methods=['POST'])
def create_payment_intent():
    """Create a Stripe payment intent"""
    data = request.json
    invoice_id = data['invoice_id']
    
    invoice = Invoice.query.get_or_404(invoice_id)
    
    try:
        intent = payment_processor.create_payment_intent(
            amount=invoice.total_amount,
            currency='usd',
            metadata={'invoice_id': invoice_id}
        )
        return jsonify({
            'client_secret': intent.get('client_secret'),
            'payment_intent_id': intent.get('id')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/payments/webhook', methods=['POST'])
def payment_webhook():
    """Handle Stripe webhook events"""
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = payment_processor.verify_webhook(payload, sig_header)
        
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            invoice_id = payment_intent['metadata'].get('invoice_id')
            
            if invoice_id:
                invoice = Invoice.query.get(int(invoice_id))
                if invoice:
                    invoice.status = 'paid'
                    invoice.payment_method = 'stripe'
                    invoice.payment_reference = payment_intent['id']
                    db.session.commit()
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/payments/ach-setup', methods=['POST'])
def setup_ach_payment():
    """Set up ACH payment for an invoice"""
    data = request.json
    invoice_id = data['invoice_id']
    
    invoice = Invoice.query.get_or_404(invoice_id)
    
    try:
        result = payment_processor.setup_ach_payment(
            amount=invoice.total_amount,
            customer_name=invoice.client.name,
            customer_email=invoice.client.email,
            metadata={'invoice_id': invoice_id}
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# Health check
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'BillOps'})


@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_file('static/index.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
