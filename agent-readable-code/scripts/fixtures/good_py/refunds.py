"""Refund issuance — small, flat, typed, specifically named."""

from dataclasses import dataclass


@dataclass
class Refund:
    id: str
    payment_id: str
    amount_cents: int


def issue_refund(payment_id: str, amount_cents: int) -> Refund:
    return Refund(id=f"ref_{payment_id}", payment_id=payment_id, amount_cents=amount_cents)


def reverse_stripe_charge(charge_id: str) -> None:
    return None
