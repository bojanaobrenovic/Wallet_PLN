"""Business logic for the wallet: PLN balance reports."""

from sqlalchemy.orm import Session

from app import models
from app.rates.service import get_exchange_rates


def get_balance_report(user_wallets, exchange_rates, effective_date):

    '''Creating a report that shows the user's balance. The report contains the balance for each currency expressed in PLN,
    as well as the user's total balance in foreign currencies (also in PLN).
    In addition, the report includes the effective date, which allows the user to see the date when the exchange rates are valid.'''

    report_list = []
    total_pln = 0.0

    for wallet in user_wallets:
        currency = wallet.currency
        amount = wallet.amount

        pln_value = amount * exchange_rates[currency]
        total_pln += pln_value

        report_list.append({
            "currency": currency,
            #"amount": amount, #useful info in report
            "value_pln": round(pln_value,2) #Two decimal places are correct for currency conversions
        })

    return {
        "wallet_report": report_list,
        "total_pln": round(total_pln,2),
        "effective_date": effective_date
    }


def process_wallet_update(db: Session, user_id: int, currency: str, wallet: models.Wallet, operation_message: str) -> dict:

    ''' Helper function for generating a report after adding or subtracting a foreign currency amount.
    The report shows:
    - the new balance in that currency expressed in PLN;
    - and the user's overall total balance in PLN across all currencies.'''

    exchange_rates, effective_date = get_exchange_rates()

    #Calculating the balance for the updated currency
    updated_in_pln = wallet.amount * exchange_rates[currency] if currency in exchange_rates else "N/A"
    wallet_report = [{
        "currency": currency,
        "amount": wallet.amount,
        "value_pln": round(updated_in_pln,2)
    }]

    #Calculating the total balance in PLN
    all_wallets = db.query(models.Wallet).filter_by(user_id=user_id).all()
    total_in_pln = sum(
        w.amount * exchange_rates[w.currency]
        for w in all_wallets if w.currency in exchange_rates
    )

    #Report after updating currency
    return {
        "message": operation_message,
        "wallet_report": wallet_report,
        "total_in_pln": round(total_in_pln,2),
        "effective_date":effective_date
    }
