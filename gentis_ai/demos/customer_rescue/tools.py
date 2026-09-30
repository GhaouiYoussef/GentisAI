from __future__ import annotations

import hashlib


ACCOUNT = {
    "account_ref": "ACCT-1042",
    "customer": "Jordan Lee",
    "plan": "Pro",
    "status": "active",
    "invoice_ref": "INV-2048",
}
INVOICE = {
    "invoice_ref": "INV-2048",
    "amount": "$49.00",
    "duplicate_charge": True,
    "status": "review eligible",
}


def lookup_account(account_ref: str) -> dict[str, object]:
    """Look up a fictional customer account."""
    if account_ref != ACCOUNT["account_ref"]:
        raise ValueError("Fictional account was not found.")
    return dict(ACCOUNT)


def check_invoice(invoice_ref: str) -> dict[str, object]:
    """Check a fictional invoice for duplicate charges."""
    if invoice_ref != INVOICE["invoice_ref"]:
        raise ValueError("Fictional invoice was not found.")
    return dict(INVOICE)


def create_support_ticket(account_ref: str, issue: str) -> dict[str, str]:
    """Create a deterministic fictional support ticket."""
    if account_ref != ACCOUNT["account_ref"]:
        raise ValueError("Fictional account was not found.")
    digest = hashlib.sha256(f"{account_ref}:{issue}".encode()).hexdigest()
    return {
        "ticket_id": f"TKT-{digest[:6].upper()}",
        "account_ref": account_ref,
        "status": "created",
        "issue": issue,
    }
