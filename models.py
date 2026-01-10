"""Database models for BillOps"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Client(db.Model):
    """Client model for managing law firm clients"""
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    matters = db.relationship('Matter', backref='client', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Matter(db.Model):
    """Matter model for managing legal matters/cases"""
    __tablename__ = 'matters'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    matter_number = db.Column(db.String(50), unique=True)
    status = db.Column(db.String(50), default='active')  # active, closed, on_hold
    hourly_rate = db.Column(db.Float, nullable=False, default=250.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    time_entries = db.relationship('TimeEntry', backref='matter', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'client_name': self.client.name if self.client else None,
            'name': self.name,
            'description': self.description,
            'matter_number': self.matter_number,
            'status': self.status,
            'hourly_rate': self.hourly_rate,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class TimeEntry(db.Model):
    """Time entry model for tracking billable hours"""
    __tablename__ = 'time_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    matter_id = db.Column(db.Integer, db.ForeignKey('matters.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    hours = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    source = db.Column(db.String(50), default='manual')  # manual, email, calendar, document
    source_reference = db.Column(db.String(500))  # Reference to source (email ID, calendar event ID, etc.)
    status = db.Column(db.String(50), default='pending')  # pending, approved, invoiced
    rate = db.Column(db.Float)  # Rate at time of entry
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'matter_id': self.matter_id,
            'matter_name': self.matter.name if self.matter else None,
            'client_name': self.matter.client.name if self.matter and self.matter.client else None,
            'description': self.description,
            'hours': self.hours,
            'date': self.date.isoformat() if self.date else None,
            'source': self.source,
            'source_reference': self.source_reference,
            'status': self.status,
            'rate': self.rate,
            'amount': self.hours * self.rate if self.rate else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'invoice_id': self.invoice_id
        }


class Invoice(db.Model):
    """Invoice model for billing clients"""
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    matter_id = db.Column(db.Integer, db.ForeignKey('matters.id'), nullable=True)
    status = db.Column(db.String(50), default='draft')  # draft, sent, paid, overdue
    total_amount = db.Column(db.Float, default=0.0)
    issue_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    due_date = db.Column(db.Date)
    payment_method = db.Column(db.String(50))  # stripe, ach, check, wire
    payment_reference = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    client = db.relationship('Client', backref='invoices')
    matter = db.relationship('Matter', backref='invoices')
    time_entries = db.relationship('TimeEntry', backref='invoice', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'client_id': self.client_id,
            'client_name': self.client.name if self.client else None,
            'matter_id': self.matter_id,
            'matter_name': self.matter.name if self.matter else None,
            'status': self.status,
            'total_amount': self.total_amount,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'payment_method': self.payment_method,
            'payment_reference': self.payment_reference,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
