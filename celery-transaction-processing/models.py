import enum

from sqlalchemy import Column, ForeignKey, Integer, String, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class UserAccount(Base):
    __tablename__ = "user_accounts"

    id = Column(Integer, primary_key=True)
    available_balance_in_wei = Column(Integer, nullable=False)
    current_balance_in_wei = Column(Integer, nullable=False)

    user_account_transactions = relationship("UserAccountTransaction", back_populates="user_account")


class UserAccountTransactionStatus(enum.Enum):
    PENDING = 0
    SUCCESSFUL = 1
    FAILED = 2


class UserAccountTransaction(Base):
    __tablename__ = "user_account_transactions"

    id = Column(Integer, primary_key=True)
    user_account_id = Column(Integer, ForeignKey("user_accounts.id"), nullable=False)
    transaction_hash = Column(String, nullable=False)
    from_public_address = Column(String, nullable=False)
    to_public_address = Column(String, nullable=False)
    transaction_amount_in_wei = Column(Integer, nullable=False)
    transaction_fee_total_in_wei = Column(Integer, nullable=False)
    transaction_fee_blockchain_in_wei = Column(Integer, nullable=False)
    status = Column(Enum(UserAccountTransactionStatus), nullable=False, default=UserAccountTransactionStatus.PENDING)

    user_account = relationship("UserAccount", back_populates="user_account_transactions")
