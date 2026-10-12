"""Business logic for the wallet: PLN balance reports."""

from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.orm import Session

from app.rates.service import ExchangeRates
from app.wallet.models import Wallet

CENT = Decimal("0.01")


def to_pln(amount: Decimal, rate: Decimal) -> Decimal:
    """Converts an amount to PLN and rounds it to whole grosze (2 decimals)."""
    return (amount * rate).quantize(CENT, rounding=ROUND_HALF_UP)


def get_balance_report(user_wallets, rates: ExchangeRates) -> dict:
    """Creates a report of the user's balance.

    The report contains the balance for each currency expressed in PLN,
    the total balance in PLN and the date the exchange rates are valid for.
    """
    report_list = []
    total_pln = Decimal("0")

    for wallet in user_wallets:
        pln_value = to_pln(wallet.amount, rates.rates[wallet.currency])
        total_pln += pln_value
        report_list.append({"currency": wallet.currency, "value_pln": pln_value})

    return {
        "wallet_report": report_list,
        "total_pln": total_pln,
        "effective_date": rates.effective_date,
    }


def process_wallet_update(
    db: Session,
    user_id: int,
    currency: str,
    wallet: Wallet,
    operation_message: str,
    rates: ExchangeRates,
) -> dict:
    """Generates a report after adding or subtracting a foreign currency amount.

    The report shows the new balance of that currency in PLN
    and the user's total balance in PLN across all currencies.
    """
    wallet_report = [
        {
            "currency": currency,
            "amount": wallet.amount,
            "value_pln": to_pln(wallet.amount, rates.rates[currency]),
        }
    ]

    all_wallets = db.query(Wallet).filter_by(user_id=user_id).all()
    total_in_pln = sum(
        (to_pln(w.amount, rates.rates[w.currency]) for w in all_wallets),
        Decimal("0"),
    )

    return {
        "message": operation_message,
        "wallet_report": wallet_report,
        "total_in_pln": total_in_pln,
        "effective_date": rates.effective_date,
    }
