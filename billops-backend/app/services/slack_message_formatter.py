"""Slack message formatting utilities and builders."""
from __future__ import annotations

from typing import Any
from datetime import datetime, timezone
from enum import Enum


class MessageColor(str, Enum):
    """Color codes for Slack messages."""

    SUCCESS = "#36a64f"
    WARNING = "#ff9900"
    ERROR = "#ff0000"
    INFO = "#0099ff"
    NEUTRAL = "#808080"


class SlackBlockBuilder:
    """Builder for Slack Block Kit messages."""

    @staticmethod
    def header(text: str) -> dict[str, Any]:
        """Create header block.

        Args:
            text: Header text

        Returns:
            Header block
        """
        return {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": text,
                "emoji": True,
            },
        }

    @staticmethod
    def section(text: str, markdown: bool = True) -> dict[str, Any]:
        """Create section block.

        Args:
            text: Section text
            markdown: Use markdown formatting

        Returns:
            Section block
        """
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn" if markdown else "plain_text",
                "text": text,
            },
        }

    @staticmethod
    def divider() -> dict[str, Any]:
        """Create divider block.

        Returns:
            Divider block
        """
        return {"type": "divider"}

    @staticmethod
    def context(elements: list[dict[str, Any]]) -> dict[str, Any]:
        """Create context block.

        Args:
            elements: List of context elements

        Returns:
            Context block
        """
        return {
            "type": "context",
            "elements": elements,
        }

    @staticmethod
    def context_text(text: str) -> dict[str, Any]:
        """Create text context element.

        Args:
            text: Text content

        Returns:
            Context text element
        """
        return {
            "type": "mrkdwn",
            "text": text,
        }

    @staticmethod
    def button(
        text: str,
        action_id: str,
        value: str,
        style: str = "default",
    ) -> dict[str, Any]:
        """Create button element.

        Args:
            text: Button text
            action_id: Action ID for callback
            value: Button value
            style: Style (default, primary, danger)

        Returns:
            Button element
        """
        button = {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": text,
                "emoji": True,
            },
            "action_id": action_id,
            "value": value,
        }

        if style in ("primary", "danger"):
            button["style"] = style

        return button

    @staticmethod
    def actions(elements: list[dict[str, Any]]) -> dict[str, Any]:
        """Create actions block.

        Args:
            elements: List of action elements

        Returns:
            Actions block
        """
        return {
            "type": "actions",
            "elements": elements,
        }

    @staticmethod
    def fields(fields: list[dict[str, Any]]) -> dict[str, Any]:
        """Create fields block.

        Args:
            fields: List of field objects

        Returns:
            Fields block
        """
        return {
            "type": "section",
            "fields": fields,
        }

    @staticmethod
    def field(title: str, value: str) -> dict[str, Any]:
        """Create field object.

        Args:
            title: Field title (bold)
            value: Field value

        Returns:
            Field object
        """
        return {
            "type": "mrkdwn",
            "text": f"*{title}*\n{value}",
        }


class SlackMessageBuilder:
    """Builder for complete Slack messages."""

    def __init__(self):
        self.blocks: list[dict[str, Any]] = []
        self.color: str | None = None

    def add_header(self, text: str) -> SlackMessageBuilder:
        """Add header block.

        Args:
            text: Header text

        Returns:
            Self for chaining
        """
        self.blocks.append(SlackBlockBuilder.header(text))
        return self

    def add_section(self, text: str, markdown: bool = True) -> SlackMessageBuilder:
        """Add section block.

        Args:
            text: Section text
            markdown: Use markdown formatting

        Returns:
            Self for chaining
        """
        self.blocks.append(SlackBlockBuilder.section(text, markdown))
        return self

    def add_divider(self) -> SlackMessageBuilder:
        """Add divider block.

        Returns:
            Self for chaining
        """
        self.blocks.append(SlackBlockBuilder.divider())
        return self

    def add_context(self, elements: list[dict[str, Any]]) -> SlackMessageBuilder:
        """Add context block.

        Args:
            elements: List of context elements

        Returns:
            Self for chaining
        """
        self.blocks.append(SlackBlockBuilder.context(elements))
        return self

    def add_context_text(self, text: str) -> SlackMessageBuilder:
        """Add context text block.

        Args:
            text: Context text

        Returns:
            Self for chaining
        """
        self.blocks.append(
            SlackBlockBuilder.context([SlackBlockBuilder.context_text(text)])
        )
        return self

    def add_fields(self, fields: list[tuple[str, str]]) -> SlackMessageBuilder:
        """Add fields block.

        Args:
            fields: List of (title, value) tuples

        Returns:
            Self for chaining
        """
        field_objects = [SlackBlockBuilder.field(title, value) for title, value in fields]
        self.blocks.append(SlackBlockBuilder.fields(field_objects))
        return self

    def add_buttons(self, buttons: list[dict[str, str]]) -> SlackMessageBuilder:
        """Add action buttons.

        Args:
            buttons: List of button dicts with keys: text, action_id, value, style

        Returns:
            Self for chaining
        """
        button_elements = [
            SlackBlockBuilder.button(
                text=btn["text"],
                action_id=btn["action_id"],
                value=btn["value"],
                style=btn.get("style", "default"),
            )
            for btn in buttons
        ]
        self.blocks.append(SlackBlockBuilder.actions(button_elements))
        return self

    def set_color(self, color: MessageColor | str) -> SlackMessageBuilder:
        """Set message color.

        Args:
            color: Color value

        Returns:
            Self for chaining
        """
        self.color = str(color)
        return self

    def build(self, text: str = "") -> dict[str, Any]:
        """Build message dict.

        Args:
            text: Fallback text

        Returns:
            Message dict for Slack API
        """
        message = {
            "text": text or "BillOps Notification",
            "blocks": self.blocks,
        }

        if self.color:
            # Add color via attachment (used for message preview)
            message["attachments"] = [
                {
                    "color": self.color,
                    "blocks": self.blocks,
                }
            ]

        return message


# Specific message formatters

def format_invoice_message(
    invoice_number: str,
    client_name: str,
    amount: float,
    currency: str = "USD",
    status: str = "sent",
) -> dict[str, Any]:
    """Format invoice notification message.

    Args:
        invoice_number: Invoice number
        client_name: Client name
        amount: Invoice amount
        currency: Currency code
        status: Invoice status

    Returns:
        Slack message dict
    """
    status_emoji = {
        "draft": "📝",
        "sent": "📤",
        "paid": "✅",
        "partial": "⚠️",
        "overdue": "🚨",
    }
    emoji = status_emoji.get(status, "📄")

    builder = SlackMessageBuilder()
    builder.add_header(f"{emoji} Invoice {invoice_number}")
    builder.add_fields([
        ("Client", client_name),
        ("Amount", f"{currency} ${amount:,.2f}"),
        ("Status", status.title()),
    ])
    builder.set_color(
        MessageColor.SUCCESS if status == "paid"
        else MessageColor.WARNING if status in ("overdue", "partial")
        else MessageColor.INFO
    )

    return builder.build(f"Invoice {invoice_number} - {client_name}")


def format_payment_message(
    invoice_number: str,
    client_name: str,
    amount: float,
    currency: str = "USD",
) -> dict[str, Any]:
    """Format payment notification message.

    Args:
        invoice_number: Invoice number
        client_name: Client name
        amount: Payment amount
        currency: Currency code

    Returns:
        Slack message dict
    """
    builder = SlackMessageBuilder()
    builder.add_header("✅ Payment Received")
    builder.add_fields([
        ("Invoice", invoice_number),
        ("Client", client_name),
        ("Amount", f"{currency} ${amount:,.2f}"),
        ("Time", datetime.now(timezone.utc).strftime("%B %d, %Y at %I:%M %p")),
    ])
    builder.set_color(MessageColor.SUCCESS)

    return builder.build(f"Payment received for {invoice_number}")


def format_time_entry_message(
    description: str,
    duration_hours: float,
    project_name: str | None = None,
    client_name: str | None = None,
) -> dict[str, Any]:
    """Format time entry notification message.

    Args:
        description: Entry description
        duration_hours: Duration in hours
        project_name: Project name (optional)
        client_name: Client name (optional)

    Returns:
        Slack message dict
    """
    fields = [
        ("Duration", f"{duration_hours:.1f} hours"),
        ("Description", description),
    ]

    if project_name:
        fields.append(("Project", project_name))
    if client_name:
        fields.append(("Client", client_name))

    builder = SlackMessageBuilder()
    builder.add_header("⏱️ Time Entry Logged")
    builder.add_fields(fields)
    builder.set_color(MessageColor.INFO)

    return builder.build("Time entry logged")


def format_daily_summary_message(
    total_hours: float,
    entry_count: int,
    date_str: str | None = None,
) -> dict[str, Any]:
    """Format daily summary message.

    Args:
        total_hours: Total hours worked
        entry_count: Number of time entries
        date_str: Date string (optional)

    Returns:
        Slack message dict
    """
    if not date_str:
        date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")

    builder = SlackMessageBuilder()
    builder.add_header("📊 Daily Time Summary")
    builder.add_fields([
        ("Date", date_str),
        ("Entries", str(entry_count)),
        ("Total Hours", f"{total_hours:.1f}"),
    ])

    # Add progress bar
    bar_length = 20
    filled = int((total_hours / 8) * bar_length)  # Assuming 8-hour workday
    filled = min(filled, bar_length)
    bar = "█" * filled + "░" * (bar_length - filled)
    builder.add_context_text(f"Daily progress: `{bar}`")

    builder.set_color(MessageColor.INFO)

    return builder.build("Daily time summary")


def format_alert_message(
    title: str,
    message: str,
    alert_type: str = "info",
) -> dict[str, Any]:
    """Format alert message.

    Args:
        title: Alert title
        message: Alert message
        alert_type: Alert type (info, warning, error, success)

    Returns:
        Slack message dict
    """
    emoji_map = {
        "success": "✅",
        "warning": "⚠️",
        "error": "🚨",
        "info": "ℹ️",
    }
    emoji = emoji_map.get(alert_type, "ℹ️")

    color_map = {
        "success": MessageColor.SUCCESS,
        "warning": MessageColor.WARNING,
        "error": MessageColor.ERROR,
        "info": MessageColor.INFO,
    }
    color = color_map.get(alert_type, MessageColor.INFO)

    builder = SlackMessageBuilder()
    builder.add_header(f"{emoji} {title}")
    builder.add_section(message)
    builder.set_color(color)

    return builder.build(title)


def format_overdue_invoice_alert(
    invoice_number: str,
    client_name: str,
    amount: float,
    days_overdue: int,
    currency: str = "USD",
) -> dict[str, Any]:
    """Format overdue invoice alert.

    Args:
        invoice_number: Invoice number
        client_name: Client name
        amount: Invoice amount
        days_overdue: Days overdue
        currency: Currency code

    Returns:
        Slack message dict
    """
    builder = SlackMessageBuilder()
    builder.add_header("🚨 Invoice Overdue")
    builder.add_fields([
        ("Invoice", invoice_number),
        ("Client", client_name),
        ("Amount", f"{currency} ${amount:,.2f}"),
        ("Overdue", f"{days_overdue} days"),
    ])

    builder.add_divider()
    builder.add_section(
        f"*Action Required:* Please follow up with {client_name} regarding payment."
    )

    builder.set_color(MessageColor.ERROR)

    return builder.build(f"Invoice {invoice_number} is overdue")


def format_invoice_details_message(
    invoice_number: str,
    client_name: str,
    project_name: str | None,
    issue_date: str,
    due_date: str | None,
    subtotal: float,
    tax: float,
    total: float,
    currency: str = "USD",
    status: str = "draft",
) -> dict[str, Any]:
    """Format detailed invoice message.

    Args:
        invoice_number: Invoice number
        client_name: Client name
        project_name: Project name (optional)
        issue_date: Issue date string
        due_date: Due date string (optional)
        subtotal: Subtotal amount
        tax: Tax amount
        total: Total amount
        currency: Currency code
        status: Invoice status

    Returns:
        Slack message dict
    """
    status_emoji = {
        "draft": "📝",
        "sent": "📤",
        "paid": "✅",
        "partial": "⚠️",
        "overdue": "🚨",
    }
    emoji = status_emoji.get(status, "📄")

    builder = SlackMessageBuilder()
    builder.add_header(f"{emoji} Invoice {invoice_number}")

    fields = [
        ("Client", client_name),
        ("Issue Date", issue_date),
    ]

    if project_name:
        fields.append(("Project", project_name))
    if due_date:
        fields.append(("Due Date", due_date))

    builder.add_fields(fields)

    builder.add_divider()

    # Add financial details
    builder.add_section(
        f"*Subtotal:* {currency} ${subtotal:,.2f}\n"
        f"*Tax:* {currency} ${tax:,.2f}\n"
        f"*Total:* {currency} ${total:,.2f}",
    )

    builder.set_color(
        MessageColor.SUCCESS if status == "paid"
        else MessageColor.WARNING if status in ("overdue", "partial")
        else MessageColor.INFO
    )

    return builder.build(f"Invoice {invoice_number}")
