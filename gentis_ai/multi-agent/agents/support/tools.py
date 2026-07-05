from __future__ import annotations


def lookup_order_status(order_id: str) -> str:
    """Example support tool for checking an order status."""

    return f"Order {order_id} is currently in progress."


def escalate_ticket(ticket_id: str, priority: str = "normal") -> str:
    """Example support tool for escalating a ticket."""

    return f"Ticket {ticket_id} escalated with {priority} priority."
