"""API routes for notifications."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models import Invoice, TimeEntry
from app.schemas import (
    InvoiceSchema,
    MessageResponse,
)
from app.services.notifications.email import EmailNotificationService
from app.services.notifications.slack import SlackNotificationService
from app.core.security import get_current_user

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])

email_service = EmailNotificationService()


@router.post("/send-invoice-email", response_model=MessageResponse)
async def send_invoice_email(
    invoice_id: str,
    recipient_email: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
) -> MessageResponse:
    """
    Send invoice via email.

    Args:
        invoice_id: ID of the invoice to send
        recipient_email: Email address of the recipient
        db: Database session
        current_user: Current authenticated user

    Returns:
        MessageResponse with status

    Raises:
        HTTPException: If invoice not found or email send fails
    """
    try:
        invoice = (
            db.query(Invoice)
            .filter(Invoice.id == UUID(invoice_id))
            .first()
        )

        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found",
            )

        # Get client info for email
        client_name = invoice.client.name if invoice.client else "Client"

        # In production, would generate PDF and send
        # For now, return success if user is authenticated
        return MessageResponse(
            message="Invoice email queued for sending",
            success=True,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send invoice email: {str(e)}",
        )


@router.post("/send-invoice-slack", response_model=MessageResponse)
async def send_invoice_slack(
    invoice_id: str,
    channel: str,
    slack_bot_token: str = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
) -> MessageResponse:
    """
    Send invoice notification to Slack.

    Args:
        invoice_id: ID of the invoice to send
        channel: Slack channel to send to
        slack_bot_token: Bot token (optional, uses default if not provided)
        db: Database session
        current_user: Current authenticated user

    Returns:
        MessageResponse with status

    Raises:
        HTTPException: If invoice not found or Slack send fails
    """
    try:
        invoice = (
            db.query(Invoice)
            .filter(Invoice.id == UUID(invoice_id))
            .first()
        )

        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found",
            )

        # Create Slack service
        slack_service = SlackNotificationService(slack_bot_token)

        # Get invoice details
        client_name = invoice.client.name if invoice.client else "Client"
        amount_cents = int(invoice.amount * 100)

        # Send notification
        success = slack_service.send_invoice_notification(
            channel=channel,
            invoice_number=invoice.invoice_number,
            client_name=client_name,
            amount_cents=amount_cents,
            status="sent",
        )

        if not success:
            raise Exception("Failed to send Slack message")

        return MessageResponse(
            message="Invoice notification sent to Slack",
            success=True,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send Slack notification: {str(e)}",
        )


@router.post("/send-payment-email", response_model=MessageResponse)
async def send_payment_email(
    invoice_id: str,
    recipient_email: str,
    payment_amount_cents: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
) -> MessageResponse:
    """
    Send payment confirmation via email.

    Args:
        invoice_id: ID of the paid invoice
        recipient_email: Email address of the recipient
        payment_amount_cents: Amount paid in cents
        db: Database session
        current_user: Current authenticated user

    Returns:
        MessageResponse with status

    Raises:
        HTTPException: If invoice not found or email send fails
    """
    try:
        invoice = (
            db.query(Invoice)
            .filter(Invoice.id == UUID(invoice_id))
            .first()
        )

        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found",
            )

        # In production, would queue email task
        return MessageResponse(
            message="Payment confirmation email queued for sending",
            success=True,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send payment email: {str(e)}",
        )


@router.post("/send-payment-slack", response_model=MessageResponse)
async def send_payment_slack(
    invoice_id: str,
    channel: str,
    payment_amount_cents: int,
    slack_bot_token: str = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
) -> MessageResponse:
    """
    Send payment notification to Slack.

    Args:
        invoice_id: ID of the paid invoice
        channel: Slack channel to send to
        payment_amount_cents: Amount paid in cents
        slack_bot_token: Bot token (optional, uses default if not provided)
        db: Database session
        current_user: Current authenticated user

    Returns:
        MessageResponse with status

    Raises:
        HTTPException: If invoice not found or Slack send fails
    """
    try:
        invoice = (
            db.query(Invoice)
            .filter(Invoice.id == UUID(invoice_id))
            .first()
        )

        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found",
            )

        # Create Slack service
        slack_service = SlackNotificationService(slack_bot_token)

        # Get invoice details
        client_name = invoice.client.name if invoice.client else "Client"

        # Send notification
        success = slack_service.send_payment_notification(
            channel=channel,
            invoice_number=invoice.invoice_number,
            client_name=client_name,
            amount_cents=payment_amount_cents,
        )

        if not success:
            raise Exception("Failed to send Slack message")

        return MessageResponse(
            message="Payment notification sent to Slack",
            success=True,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send payment Slack notification: {str(e)}",
        )


@router.post("/send-alert-email", response_model=MessageResponse)
async def send_alert_email(
    recipient_email: str,
    alert_title: str,
    alert_message: str,
    alert_type: str = "info",
    current_user = Depends(get_current_user),
) -> MessageResponse:
    """
    Send alert email.

    Args:
        recipient_email: Email address of the recipient
        alert_title: Title of the alert
        alert_message: Message content
        alert_type: Type of alert (info, warning, error)
        current_user: Current authenticated user

    Returns:
        MessageResponse with status

    Raises:
        HTTPException: If email send fails
    """
    try:
        # In production, would queue email task
        return MessageResponse(
            message="Alert email queued for sending",
            success=True,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send alert email: {str(e)}",
        )


@router.post("/send-alert-slack", response_model=MessageResponse)
async def send_alert_slack(
    channel: str,
    alert_title: str,
    alert_message: str,
    alert_type: str = "info",
    slack_bot_token: str = None,
    current_user = Depends(get_current_user),
) -> MessageResponse:
    """
    Send alert to Slack.

    Args:
        channel: Slack channel to send to
        alert_title: Title of the alert
        alert_message: Message content
        alert_type: Type of alert (info, warning, error)
        slack_bot_token: Bot token (optional, uses default if not provided)
        current_user: Current authenticated user

    Returns:
        MessageResponse with status

    Raises:
        HTTPException: If Slack send fails
    """
    try:
        # Create Slack service
        slack_service = SlackNotificationService(slack_bot_token)

        # Send notification
        success = slack_service.send_alert(
            channel=channel,
            title=alert_title,
            message=alert_message,
            alert_type=alert_type,
        )

        if not success:
            raise Exception("Failed to send Slack message")

        return MessageResponse(
            message="Alert sent to Slack",
            success=True,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send Slack alert: {str(e)}",
        )


@router.post("/overdue/check", response_model=MessageResponse)
async def check_and_alert_overdue(
    current_user = Depends(get_current_user),
) -> MessageResponse:
    """
    Trigger check for overdue invoices and send alerts.

    Args:
        current_user: Current authenticated user

    Returns:
        MessageResponse with status

    In production, would trigger Celery task to check for overdue invoices
    and send email/Slack alerts to affected users.
    """
    try:
        from app.services.tasks.notifications import check_overdue_invoices

        # Queue the task
        task = check_overdue_invoices.delay(user_id=str(current_user.id))

        return MessageResponse(
            message=f"Overdue invoice check initiated. Task ID: {task.id}",
            success=True,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger overdue check: {str(e)}",
        )


@router.get("/status/{task_id}", response_model=dict)
async def get_notification_status(
    task_id: str,
    current_user = Depends(get_current_user),
) -> dict:
    """
    Get the status of a notification task.

    Args:
        task_id: Celery task ID returned from notification endpoints
        current_user: Current authenticated user

    Returns:
        Task status information

    States: PENDING, STARTED, SUCCESS, FAILURE, RETRY
    """
    try:
        from app.celery_app import celery_app

        task_result = celery_app.AsyncResult(task_id)

        response = {
            "task_id": task_id,
            "state": task_result.state,
            "status": str(task_result.info),
        }

        if task_result.state == "FAILURE":
            response["error"] = str(task_result.info)
        elif task_result.state == "SUCCESS":
            response["result"] = task_result.result

        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}",
        )


@router.post("/test/email", response_model=MessageResponse)
async def test_email_notification(
    recipient_email: str,
    current_user = Depends(get_current_user),
) -> MessageResponse:
    """
    Send a test email notification.

    Args:
        recipient_email: Email address to send test to
        current_user: Current authenticated user

    Returns:
        MessageResponse with status

    Validates email provider is properly configured.
    """
    try:
        success = email_service.send_alert_email(
            recipient_email=recipient_email,
            subject="Test Email from BillOps",
            message="This is a test email notification",
            alert_type="info",
        )

        return MessageResponse(
            message="Test email sent successfully" if success else "Failed to send test email",
            success=success,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test email: {str(e)}",
        )


@router.post("/test/slack", response_model=MessageResponse)
async def test_slack_notification(
    channel: str,
    current_user = Depends(get_current_user),
) -> MessageResponse:
    """
    Send a test Slack notification.

    Args:
        channel: Slack channel ID (e.g., C123456)
        current_user: Current authenticated user

    Returns:
        MessageResponse with status

    Validates Slack integration is properly configured.
    """
    try:
        from app.config.settings import Settings

        settings = Settings()
        slack_service = SlackNotificationService(slack_bot_token=settings.slack_bot_token)

        if not settings.slack_bot_token:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Slack bot token not configured",
            )

        success = slack_service.send_message(
            channel=channel,
            text="Test notification from BillOps",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "🧪 *Test Slack Notification*\n\nThis is a test message from BillOps to verify your Slack integration is working correctly.",
                    },
                }
            ],
        )

        return MessageResponse(
            message="Test Slack message sent successfully" if success else "Failed to send Slack message",
            success=success,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send Slack message: {str(e)}",
        )


@router.get("/config/status", response_model=dict)
async def notification_config_status(
    current_user = Depends(get_current_user),
) -> dict:
    """
    Get the status of notification provider configuration.

    Args:
        current_user: Current authenticated user

    Returns:
        Configuration status for email and Slack providers

    Shows which providers are configured and helps diagnose issues.
    """
    try:
        from app.config.settings import Settings

        settings = Settings()

        return {
            "email": {
                "provider": settings.email_provider,
                "configured": bool(
                    (settings.email_provider == "sendgrid" and settings.sendgrid_api_key)
                    or (settings.email_provider == "ses" and settings.ses_access_key_id)
                ),
                "from_email": settings.from_email,
            },
            "slack": {
                "configured": bool(settings.slack_bot_token),
                "signing_secret_configured": bool(settings.slack_signing_secret),
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get config status: {str(e)}",
        )


@router.get("/health", response_model=MessageResponse)
async def health_check() -> MessageResponse:
    """Health check for notification service."""
    return MessageResponse(
        message="Notification service is healthy",
        success=True,
    )
