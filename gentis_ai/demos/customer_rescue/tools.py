from __future__ import annotations

from uuid import uuid4


ACCOUNT_REF = "ACCT-1042"
ACCOUNT = {"customer": "Youssef Ghaoui"}
INVOICE = {
    "invoice_ref": "INV-2048",
    "amount": "$49.00",
    "duplicate_charge": True,
    "status": "review eligible",
}


def lookup_account(account_ref: str) -> dict[str, object]:
    """Look up a fictional customer account."""
    if account_ref != ACCOUNT_REF:
        raise ValueError("Fictional account was not found.")
    return dict(ACCOUNT)


def check_invoice(invoice_ref: str) -> dict[str, object]:
    """Check a fictional invoice for duplicate charges."""
    if invoice_ref != INVOICE["invoice_ref"]:
        raise ValueError("Fictional invoice was not found.")
    return dict(INVOICE)


def create_support_ticket(account_ref: str, issue: str) -> dict[str, str]:
    """Create a new demo ticket for the supplied customer issue."""
    if account_ref != ACCOUNT_REF:
        raise ValueError("Fictional account was not found.")
    if not issue.strip():
        raise ValueError("A ticket issue is required.")
    return {
        "ticket_id": f"TKT-{uuid4().hex.upper()}",
        "account_ref": account_ref,
        "status": "created",
        "issue": issue,
    }
