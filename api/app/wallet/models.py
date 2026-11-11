"""Database table for wallet balances (one row per user and currency)."""

from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.core.database import Base

# Available currencies - created based on available currencies in API NLB which contain 'ask' values
SUPPORTED_CURRENCIES = [
    "USD",
    "AUD",
    "CAD",
    "EUR",
    "HUF",
    "CHF",
    "GBP",
    "JPY",
    "CZK",
    "DKK",
    "NOK",
    "SEK",
    "XDR",
]


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    currency = Column(String, index=True, nullable=False)
    amount = Column(Numeric(18, 2), default=0, nullable=False)

    owner = relationship("User", back_populates="wallets")

    __table_args__ = (
        CheckConstraint("amount >= 0", name="amount_non_negative"),
        CheckConstraint(f"currency IN {tuple(SUPPORTED_CURRENCIES)}", name="valid_currency"),
    )

    def __repr__(self):
        return (
            f"<Wallet(id={self.id}, user_id={self.user_id},"
            f" currency={self.currency}, amount={self.amount})>"
        )
