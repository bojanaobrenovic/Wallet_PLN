from . import database
from .database import Base

from sqlalchemy import Column, Integer, String, Float, ForeignKey,CheckConstraint
from sqlalchemy.orm import relationship


#Available currencies - created based on available currencies in API NLB which contain 'ask' values
SUPPORTED_CURRENCIES = ['USD', 'AUD', 'CAD', 'EUR', 'HUF', 'CHF', 'GBP', 'JPY', 'CZK', 'DKK', 'NOK', 'SEK', 'XDR']

#Users
class User(Base):
    __tablename__= "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String(250), unique=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False) #hash password

    wallets = relationship("Wallet", back_populates="owner", cascade="all, delete-orphan")


    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"


#Wallets
class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    currency = Column(String, index=True, nullable=False)
    amount = Column(Float, default=0.0, nullable=False)

    owner = relationship("User", back_populates="wallets")


    __table_args__ = (
        CheckConstraint("amount >= 0", name="amount_non_negative"),
        CheckConstraint(f"currency IN {tuple(SUPPORTED_CURRENCIES)}", name="valid_currency"),
    )

    def __repr__(self):
        return f"<Wallet(id={self.id}, user_id={self.user_id}, currency={self.currency}, amount={self.amount})>"

