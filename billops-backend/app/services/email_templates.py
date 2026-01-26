"""Email template generators for invoices, payments, and alerts."""
from typing import Dict, Any, Optional
from datetime import datetime


class EmailTemplates:
    """Email template generators with HTML and text versions."""

    @staticmethod
    def invoice_template(
        client_name: str,
        invoice_number: str,
        invoice_date: datetime,
        due_date: Optional[datetime],
        total_amount: float,
        currency: str = "USD",
        items: Optional[list[Dict[str, Any]]] = None,
        company_name: str = "BillOps",
        company_email: str = "noreply@billops.com",
        footer_text: Optional[str] = None,
    ) -> Dict[str, str]:
        """Generate professional invoice email template.

        Args:
            client_name: Client/recipient name
            invoice_number: Invoice number
            invoice_date: Invoice date
            due_date: Payment due date
            total_amount: Total invoice amount
            currency: Currency code (USD, EUR, etc.)
            items: List of line items with description, quantity, rate
            company_name: Company/sender name
            company_email: Company email
            footer_text: Custom footer text

        Returns:
            Dict with 'html' and 'text' keys containing email content
        """
        invoice_date_str = invoice_date.strftime("%B %d, %Y")
        due_date_str = due_date.strftime("%B %d, %Y") if due_date else "Upon receipt"
        currency_symbol = "$" if currency == "USD" else currency

        # Build items table if provided
        items_html = ""
        items_text = ""
        if items:
            items_html = "<tr><th>Description</th><th>Qty</th><th>Rate</th><th>Amount</th></tr>"
            items_text = "Description | Qty | Rate | Amount\n"
            items_text += "---|---|---|---\n"

            for item in items:
                qty = item.get("quantity", 1)
                rate = item.get("rate", 0)
                amount = qty * rate
                items_html += (
                    f"<tr><td>{item.get('description', '')}</td>"
                    f"<td>{qty}</td><td>{currency_symbol}{rate:,.2f}</td>"
                    f"<td>{currency_symbol}{amount:,.2f}</td></tr>"
                )
                items_text += (
                    f"{item.get('description', '')} | {qty} | "
                    f"{currency_symbol}{rate:,.2f} | {currency_symbol}{amount:,.2f}\n"
                )

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    color: #333;
                    line-height: 1.6;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f9f9f9;
                }}
                .header {{
                    background-color: #2c3e50;
                    color: #fff;
                    padding: 30px;
                    text-align: center;
                    border-radius: 8px 8px 0 0;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                }}
                .header p {{
                    margin: 10px 0 0 0;
                    font-size: 14px;
                    opacity: 0.9;
                }}
                .content {{
                    background-color: #fff;
                    padding: 30px;
                    border: 1px solid #ddd;
                }}
                .invoice-details {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                .detail-box {{
                    padding: 15px;
                    background-color: #f5f5f5;
                    border-radius: 4px;
                }}
                .detail-label {{
                    font-weight: bold;
                    color: #2c3e50;
                    font-size: 12px;
                    text-transform: uppercase;
                    margin-bottom: 5px;
                }}
                .detail-value {{
                    font-size: 16px;
                    color: #333;
                }}
                .items-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }}
                .items-table th {{
                    background-color: #ecf0f1;
                    padding: 12px;
                    text-align: left;
                    font-weight: bold;
                    border-bottom: 2px solid #2c3e50;
                }}
                .items-table td {{
                    padding: 12px;
                    border-bottom: 1px solid #ddd;
                }}
                .items-table tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                .summary {{
                    text-align: right;
                    margin-top: 20px;
                    border-top: 2px solid #ddd;
                    padding-top: 20px;
                }}
                .summary-row {{
                    display: flex;
                    justify-content: flex-end;
                    margin-bottom: 10px;
                }}
                .summary-label {{
                    width: 150px;
                    font-weight: bold;
                    color: #333;
                }}
                .summary-value {{
                    width: 100px;
                    text-align: right;
                    color: #333;
                }}
                .total {{
                    font-size: 18px;
                    font-weight: bold;
                    color: #2c3e50;
                }}
                .cta {{
                    background-color: #27ae60;
                    color: white;
                    padding: 15px;
                    text-align: center;
                    border-radius: 4px;
                    margin-top: 30px;
                }}
                .cta a {{
                    color: white;
                    text-decoration: none;
                    font-weight: bold;
                }}
                .footer {{
                    background-color: #ecf0f1;
                    padding: 20px;
                    text-align: center;
                    font-size: 12px;
                    color: #666;
                    border-radius: 0 0 8px 8px;
                    border: 1px solid #ddd;
                    border-top: none;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Invoice</h1>
                    <p>Thank you for your business</p>
                </div>

                <div class="content">
                    <p>Dear {client_name},</p>

                    <p>Please find your invoice details below. Thank you for your business!</p>

                    <div class="invoice-details">
                        <div class="detail-box">
                            <div class="detail-label">Invoice Number</div>
                            <div class="detail-value">{invoice_number}</div>
                        </div>
                        <div class="detail-box">
                            <div class="detail-label">Invoice Date</div>
                            <div class="detail-value">{invoice_date_str}</div>
                        </div>
                        <div class="detail-box">
                            <div class="detail-label">Due Date</div>
                            <div class="detail-value">{due_date_str}</div>
                        </div>
                        <div class="detail-box">
                            <div class="detail-label">Total Due</div>
                            <div class="detail-value" style="color: #27ae60; font-size: 20px;">
                                {currency_symbol}{total_amount:,.2f}
                            </div>
                        </div>
                    </div>

                    {f'<table class="items-table"><tbody>{items_html}</tbody></table>' if items_html else ''}

                    <div class="summary">
                        <div class="summary-row">
                            <div class="summary-label">Total Amount:</div>
                            <div class="summary-value total">{currency_symbol}{total_amount:,.2f}</div>
                        </div>
                    </div>

                    <div class="cta">
                        <a href="#">View Full Invoice & Pay</a>
                    </div>

                    <p style="margin-top: 30px; font-size: 14px; color: #666;">
                        If you have any questions about this invoice, please don't hesitate to contact us.
                    </p>
                </div>

                <div class="footer">
                    <p>{company_name} | {company_email}</p>
                    {f'<p>{footer_text}</p>' if footer_text else ''}
                    <p>&copy; {datetime.now().year} {company_name}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
INVOICE

Dear {client_name},

Invoice Number: {invoice_number}
Invoice Date: {invoice_date_str}
Due Date: {due_date_str}

{items_text if items_text else ''}

TOTAL AMOUNT DUE: {currency_symbol}{total_amount:,.2f}

If you have any questions about this invoice, please don't hesitate to contact us.

Best regards,
{company_name}
{company_email}
"""

        return {"html": html_content, "text": text_content}

    @staticmethod
    def payment_confirmation_template(
        client_name: str,
        invoice_number: str,
        payment_amount: float,
        payment_date: datetime,
        currency: str = "USD",
    ) -> Dict[str, str]:
        """Generate payment confirmation email template.

        Args:
            client_name: Client name
            invoice_number: Invoice number
            payment_amount: Payment amount
            payment_date: Payment date
            currency: Currency code

        Returns:
            Dict with 'html' and 'text' keys
        """
        payment_date_str = payment_date.strftime("%B %d, %Y")
        currency_symbol = "$" if currency == "USD" else currency

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    color: #333;
                    line-height: 1.6;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .success-box {{
                    background-color: #d4edda;
                    border: 1px solid #c3e6cb;
                    color: #155724;
                    padding: 20px;
                    border-radius: 4px;
                    margin-bottom: 30px;
                    text-align: center;
                }}
                .success-box h2 {{
                    margin-top: 0;
                    color: #155724;
                }}
                .details {{
                    background-color: #f5f5f5;
                    padding: 20px;
                    border-radius: 4px;
                    margin-bottom: 20px;
                }}
                .detail-row {{
                    display: flex;
                    justify-content: space-between;
                    padding: 10px 0;
                    border-bottom: 1px solid #ddd;
                }}
                .detail-row:last-child {{
                    border-bottom: none;
                }}
                .detail-label {{
                    font-weight: bold;
                    color: #2c3e50;
                }}
                .detail-value {{
                    color: #555;
                }}
                .footer {{
                    text-align: center;
                    color: #666;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success-box">
                    <h2>✓ Payment Received</h2>
                    <p>Your payment has been successfully processed.</p>
                </div>

                <p>Dear {client_name},</p>

                <p>Thank you for your payment. We have received your payment and have applied it to your account.</p>

                <div class="details">
                    <div class="detail-row">
                        <div class="detail-label">Invoice Number:</div>
                        <div class="detail-value">{invoice_number}</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">Payment Amount:</div>
                        <div class="detail-value">{currency_symbol}{payment_amount:,.2f}</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">Payment Date:</div>
                        <div class="detail-value">{payment_date_str}</div>
                    </div>
                </div>

                <p>Your account has been updated with this payment. If you have any questions, please contact us.</p>

                <div class="footer">
                    <p>&copy; {datetime.now().year}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
PAYMENT RECEIVED

Dear {client_name},

Thank you for your payment. We have received your payment and have applied it to your account.

Invoice Number: {invoice_number}
Payment Amount: {currency_symbol}{payment_amount:,.2f}
Payment Date: {payment_date_str}

Your account has been updated with this payment. If you have any questions, please contact us.

Best regards,
BillOps
"""

        return {"html": html_content, "text": text_content}

    @staticmethod
    def overdue_invoice_template(
        client_name: str,
        invoice_number: str,
        amount_due: float,
        days_overdue: int,
        due_date: datetime,
        currency: str = "USD",
    ) -> Dict[str, str]:
        """Generate overdue invoice reminder email template.

        Args:
            client_name: Client name
            invoice_number: Invoice number
            amount_due: Amount still due
            days_overdue: Days overdue
            due_date: Original due date
            currency: Currency code

        Returns:
            Dict with 'html' and 'text' keys
        """
        due_date_str = due_date.strftime("%B %d, %Y")
        currency_symbol = "$" if currency == "USD" else currency

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    color: #333;
                    line-height: 1.6;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .warning-box {{
                    background-color: #fff3cd;
                    border: 1px solid #ffc107;
                    color: #856404;
                    padding: 20px;
                    border-radius: 4px;
                    margin-bottom: 30px;
                }}
                .warning-box h2 {{
                    margin-top: 0;
                    color: #856404;
                }}
                .alert-text {{
                    background-color: #fff8e1;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin-bottom: 20px;
                    border-radius: 4px;
                }}
                .details {{
                    background-color: #f5f5f5;
                    padding: 20px;
                    border-radius: 4px;
                    margin-bottom: 20px;
                }}
                .detail-row {{
                    display: flex;
                    justify-content: space-between;
                    padding: 10px 0;
                }}
                .detail-label {{
                    font-weight: bold;
                    color: #2c3e50;
                }}
                .detail-value {{
                    color: #555;
                }}
                .cta {{
                    background-color: #e74c3c;
                    color: white;
                    padding: 15px;
                    text-align: center;
                    border-radius: 4px;
                    margin-top: 30px;
                }}
                .cta a {{
                    color: white;
                    text-decoration: none;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="warning-box">
                    <h2>⚠️ Invoice Payment Overdue</h2>
                    <p>This invoice is now {days_overdue} days past due.</p>
                </div>

                <p>Dear {client_name},</p>

                <div class="alert-text">
                    <strong>Invoice {invoice_number} is overdue.</strong> Please remit payment as soon as possible.
                </div>

                <div class="details">
                    <div class="detail-row">
                        <div class="detail-label">Invoice Number:</div>
                        <div class="detail-value">{invoice_number}</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">Original Due Date:</div>
                        <div class="detail-value">{due_date_str}</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">Days Overdue:</div>
                        <div class="detail-value">{days_overdue}</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">Amount Due:</div>
                        <div class="detail-value" style="color: #e74c3c; font-weight: bold;">
                            {currency_symbol}{amount_due:,.2f}
                        </div>
                    </div>
                </div>

                <p>We appreciate your prompt attention to this matter. If you have any questions or need to discuss payment arrangements, please contact us immediately.</p>

                <div class="cta">
                    <a href="#">Pay Now</a>
                </div>

                <p style="font-size: 12px; color: #666; margin-top: 30px;">
                    If you have already sent this payment, please disregard this notice.
                </p>
            </div>
        </body>
        </html>
        """

        text_content = f"""
INVOICE PAYMENT OVERDUE

Dear {client_name},

Invoice {invoice_number} is now {days_overdue} days overdue. Please remit payment as soon as possible.

Invoice Number: {invoice_number}
Original Due Date: {due_date_str}
Days Overdue: {days_overdue}
Amount Due: {currency_symbol}{amount_due:,.2f}

We appreciate your prompt attention to this matter. If you have any questions or need to discuss payment arrangements, please contact us immediately.

If you have already sent this payment, please disregard this notice.

Best regards,
BillOps
"""

        return {"html": html_content, "text": text_content}

    @staticmethod
    def time_entry_summary_template(
        user_name: str,
        summary_date: datetime,
        total_hours: float,
        entry_count: int,
        entries: Optional[list[Dict[str, Any]]] = None,
    ) -> Dict[str, str]:
        """Generate time entry summary email template.

        Args:
            user_name: User name
            summary_date: Date of summary
            total_hours: Total hours logged
            entry_count: Number of entries
            entries: List of time entries with description and hours

        Returns:
            Dict with 'html' and 'text' keys
        """
        date_str = summary_date.strftime("%B %d, %Y")

        entries_html = ""
        entries_text = ""
        if entries:
            entries_html = "<ul style='list-style-position: inside; color: #555;'>"
            for entry in entries:
                hours = entry.get("hours", 0)
                description = entry.get("description", "Work")
                entries_html += f"<li>{description}: {hours:.2f} hours</li>"
                entries_text += f"• {description}: {hours:.2f} hours\n"
            entries_html += "</ul>"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    color: #333;
                    line-height: 1.6;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .info-box {{
                    background-color: #e3f2fd;
                    border: 1px solid #90caf9;
                    color: #1565c0;
                    padding: 20px;
                    border-radius: 4px;
                    margin-bottom: 30px;
                }}
                .summary {{
                    background-color: #f5f5f5;
                    padding: 20px;
                    border-radius: 4px;
                    margin-bottom: 20px;
                }}
                .summary-item {{
                    display: flex;
                    justify-content: space-between;
                    padding: 10px 0;
                    border-bottom: 1px solid #ddd;
                }}
                .summary-item:last-child {{
                    border-bottom: none;
                }}
                .label {{
                    font-weight: bold;
                    color: #2c3e50;
                }}
                .value {{
                    color: #555;
                }}
                .total-hours {{
                    font-size: 20px;
                    font-weight: bold;
                    color: #27ae60;
                    text-align: center;
                    padding-top: 20px;
                    border-top: 2px solid #ddd;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="info-box">
                    <h2 style="margin-top: 0;">Daily Time Summary</h2>
                    <p>Here's a summary of your time entries for {date_str}.</p>
                </div>

                <p>Hi {user_name},</p>

                <div class="summary">
                    <div class="summary-item">
                        <div class="label">Date:</div>
                        <div class="value">{date_str}</div>
                    </div>
                    <div class="summary-item">
                        <div class="label">Entries:</div>
                        <div class="value">{entry_count}</div>
                    </div>
                    <div class="summary-item">
                        <div class="label">Total Hours:</div>
                        <div class="value" style="color: #27ae60; font-weight: bold;">{total_hours:.2f}</div>
                    </div>
                </div>

                {f'<h3>Time Entries</h3>{entries_html}' if entries_html else ''}

                <p style="font-size: 14px; color: #666; margin-top: 30px;">
                    This is an automated summary email. Please review your time entries and make any necessary corrections.
                </p>
            </div>
        </body>
        </html>
        """

        text_content = f"""
DAILY TIME SUMMARY

Hi {user_name},

Here's a summary of your time entries for {date_str}.

Date: {date_str}
Number of Entries: {entry_count}
Total Hours: {total_hours:.2f}

{f'Time Entries:\n{entries_text}' if entries_text else ''}

This is an automated summary email. Please review your time entries and make any necessary corrections.

Best regards,
BillOps
"""

        return {"html": html_content, "text": text_content}
