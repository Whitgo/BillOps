"""Invoice PDF generation module"""
import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_RIGHT, TA_CENTER


# Constants
MAX_DESCRIPTION_LENGTH = 60


def generate_invoice_pdf(invoice, time_entries):
    """
    Generate a PDF invoice
    
    Args:
        invoice: Invoice model instance
        time_entries: List of TimeEntry model instances
    
    Returns:
        Path to the generated PDF file
    """
    # Create invoices directory if it doesn't exist
    invoices_dir = os.path.join(os.path.dirname(__file__), 'invoices')
    os.makedirs(invoices_dir, exist_ok=True)
    
    # Create PDF file path
    pdf_filename = f"{invoice.invoice_number}.pdf"
    pdf_path = os.path.join(invoices_dir, pdf_filename)
    
    # Create the PDF document
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Add custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=12,
    )
    
    right_align_style = ParagraphStyle(
        'RightAlign',
        parent=styles['Normal'],
        alignment=TA_RIGHT,
    )
    
    # Title
    title = Paragraph("INVOICE", title_style)
    story.append(title)
    story.append(Spacer(1, 0.2*inch))
    
    # Invoice header information
    header_data = [
        ['Invoice Number:', invoice.invoice_number],
        ['Issue Date:', invoice.issue_date.strftime('%B %d, %Y')],
        ['Due Date:', invoice.due_date.strftime('%B %d, %Y') if invoice.due_date else 'Upon Receipt'],
        ['Status:', invoice.status.upper()],
    ]
    
    header_table = Table(header_data, colWidths=[2*inch, 3*inch])
    header_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Bill To section
    bill_to_heading = Paragraph("BILL TO:", heading_style)
    story.append(bill_to_heading)
    
    client_info = []
    client_info.append(invoice.client.name)
    if invoice.client.email:
        client_info.append(invoice.client.email)
    if invoice.client.phone:
        client_info.append(invoice.client.phone)
    if invoice.client.address:
        client_info.append(invoice.client.address)
    
    for line in client_info:
        story.append(Paragraph(line, styles['Normal']))
    
    story.append(Spacer(1, 0.3*inch))
    
    # Matter information if available
    if invoice.matter:
        matter_heading = Paragraph("MATTER:", heading_style)
        story.append(matter_heading)
        story.append(Paragraph(f"{invoice.matter.name} ({invoice.matter.matter_number})", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
    
    # Time entries table
    entries_heading = Paragraph("TIME ENTRIES:", heading_style)
    story.append(entries_heading)
    story.append(Spacer(1, 0.1*inch))
    
    # Table headers
    table_data = [
        ['Date', 'Description', 'Hours', 'Rate', 'Amount']
    ]
    
    # Add time entries
    for entry in time_entries:
        description = entry.description
        if len(description) > MAX_DESCRIPTION_LENGTH:
            description = description[:MAX_DESCRIPTION_LENGTH] + '...'
        
        table_data.append([
            entry.date.strftime('%m/%d/%Y'),
            description,
            f"{entry.hours:.2f}",
            f"${entry.rate:.2f}",
            f"${entry.hours * entry.rate:.2f}"
        ])
    
    # Add total row
    table_data.append(['', '', '', 'TOTAL:', f"${invoice.total_amount:.2f}"])
    
    # Create table
    col_widths = [1*inch, 3.5*inch, 0.8*inch, 0.8*inch, 1*inch]
    entries_table = Table(table_data, colWidths=col_widths)
    
    # Style the table
    table_style = TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Data rows
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -2), 9),
        ('ALIGN', (2, 1), (2, -2), 'CENTER'),
        ('ALIGN', (3, 1), (3, -2), 'RIGHT'),
        ('ALIGN', (4, 1), (4, -2), 'RIGHT'),
        ('VALIGN', (0, 1), (-1, -2), 'TOP'),
        ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
        
        # Alternate row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8f9fa')]),
        
        # Total row
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 11),
        ('ALIGN', (3, -1), (3, -1), 'RIGHT'),
        ('ALIGN', (4, -1), (4, -1), 'RIGHT'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ecf0f1')),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#34495e')),
        ('TOPPADDING', (0, -1), (-1, -1), 12),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 12),
    ])
    
    entries_table.setStyle(table_style)
    story.append(entries_table)
    story.append(Spacer(1, 0.4*inch))
    
    # Notes section if available
    if invoice.notes:
        notes_heading = Paragraph("NOTES:", heading_style)
        story.append(notes_heading)
        notes_text = Paragraph(invoice.notes, styles['Normal'])
        story.append(notes_text)
        story.append(Spacer(1, 0.3*inch))
    
    # Payment information
    payment_heading = Paragraph("PAYMENT INFORMATION:", heading_style)
    story.append(payment_heading)
    
    payment_info = [
        "Payment is due within 30 days of the invoice date.",
        "Accepted payment methods: Credit Card (Stripe), ACH Transfer, Check, Wire Transfer",
    ]
    
    for line in payment_info:
        story.append(Paragraph(line, styles['Normal']))
    
    story.append(Spacer(1, 0.2*inch))
    
    # Footer
    footer_text = Paragraph(
        "Thank you for your business!",
        ParagraphStyle('Footer', parent=styles['Normal'], alignment=TA_CENTER, textColor=colors.grey)
    )
    story.append(Spacer(1, 0.3*inch))
    story.append(footer_text)
    
    # Build PDF
    doc.build(story)
    
    return pdf_path
