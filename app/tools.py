# app/tools.py

"""Utility tools for the shopping‑assistant agent.

This module defines the ``process_cart_checkout`` tool that receives a cart ID
and a discount code, applies the discount, creates an order, and returns a
summary dictionary.  The implementation uses simple in‑memory stores for
carts, discounts, and orders – sufficient for demonstration and unit testing.

The tool is registered in ``app/agent.py`` via the ``tools`` list.
"""

from __future__ import annotations

from typing import Dict, Any
from pydantic import BaseModel, Field, validator
import uuid

# ---------------------------------------------------------------------------
# Simple in‑memory stores (replace with a database in production)
# ---------------------------------------------------------------------------
CART_STORE: Dict[str, Dict[str, Any]] = {
    "cart123": {"items": [{"product": "Widget", "price": 20.0, "qty": 2}], "processed": False},
    "cart456": {"items": [{"product": "Gadget", "price": 15.0, "qty": 1}], "processed": False},
}

DISCOUNT_CODES: Dict[str, int] = {
    "WELCOME50": 50,
    "SAVE10": 10,
    "HALF": 50,
}

# Track which (user, code) pairs have already been redeemed
redeemed_codes: set[tuple[str, str]] = set()

# Discount redemption tool

def redeem_discount_code(user_id: str, code: str) -> str:
    """Redeem a single‑use discount code.

    * Validates that ``code`` exists in ``DISCOUNT_CODES``.
    * Ensures the pair ``(user_id, code)`` has not been used before.
    * Returns a friendly message indicating success or the relevant failure.
    """
    # Runtime type validation to enforce string inputs
    if not isinstance(user_id, str):
        raise TypeError("user_id must be a string")
    if not isinstance(code, str):
        raise TypeError("code must be a string")
    normalized = code.upper().strip()
    if normalized not in DISCOUNT_CODES:
        return f"❌ Code '{code}' is invalid."
    key = (user_id, normalized)
    if key in redeemed_codes:
        return f"⚠️ Code '{code}' has already been redeemed by this user."
    redeemed_codes.add(key)
    discount = DISCOUNT_CODES[normalized]
    return f"✅ Success! You've received a {discount}% discount."


ORDER_STORE: Dict[str, Dict[str, Any]] = {}

# ---------------------------------------------------------------------------
# Pydantic model for tool input validation (secure‑by‑default)
# ---------------------------------------------------------------------------
class ProcessCartCheckoutInput(BaseModel):
    """Input schema for ``process_cart_checkout``.

    The secure‑coding policy requires all tools to validate their inputs using
    Pydantic models.
    """

    cart_id: str = Field(..., description="Identifier of the shopping cart to checkout")
    discount_code: str = Field(..., description="Discount code to apply (must exist in DISCOUNT_CODES)")

    @validator("cart_id")
    def cart_must_exist(cls, v: str) -> str:
        if v not in CART_STORE:
            raise ValueError(f"Cart ID '{v}' does not exist")
        return v

    @validator("discount_code")
    def discount_must_be_valid(cls, v: str) -> str:
        if v not in DISCOUNT_CODES:
            raise ValueError(f"Discount code '{v}' is invalid")
        return v

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def _calculate_cart_total(cart: Dict[str, Any]) -> float:
    """Calculate the raw total for a cart (price × quantity)."""
    return sum(item["price"] * item["qty"] for item in cart["items"])

# ---------------------------------------------------------------------------
# Tool implementation
# ---------------------------------------------------------------------------
def process_cart_checkout(input: ProcessCartCheckoutInput) -> Dict[str, Any]:
    """Process a checkout.

    Steps:
    1. Validate the input via the ``ProcessCartCheckoutInput`` model (already
       performed by Pydantic when the tool is invoked).
    2. Ensure the cart has not been processed already.
    3. Compute the total, apply the discount, and create an order record.
    4. Mark the cart as processed.
    5. Return a dictionary summarising the order.
    """

    # Retrieve and validate the cart
    cart = CART_STORE[input.cart_id]
    if cart.get("processed"):
        raise ValueError(f"Cart '{input.cart_id}' has already been processed")

    # Compute totals
    raw_total = _calculate_cart_total(cart)
    discount_percent = DISCOUNT_CODES[input.discount_code]
    discount_amount = raw_total * discount_percent / 100
    final_total = round(raw_total - discount_amount, 2)

    # Create order
    order_id = str(uuid.uuid4())
    order = {
        "order_id": order_id,
        "cart_id": input.cart_id,
        "items": cart["items"],
        "raw_total": raw_total,
        "discount_code": input.discount_code,
        "discount_rate": discount_percent,
        "discount_amount": discount_amount,
        "final_total": final_total,
        "status": "completed",
    }
    ORDER_STORE[order_id] = order

    # Mark cart as processed
    cart["processed"] = True

    return order

__all__ = ["process_cart_checkout", "ProcessCartCheckoutInput", "redeem_discount_code", "DISCOUNT_CODES", "redeemed_codes"]
