"""Expense model for tracking shared expenses."""

from typing import Dict, Any, List
from datetime import datetime
import uuid
from enum import Enum


class SplitType(Enum):
    """Types of expense splitting."""
    EQUAL = "equal"
    EXACT = "exact"
    PERCENTAGE = "percentage"


class Expense:
    """Represents an expense that can be split among users."""
    
    def __init__(self, amount: float, description: str, paid_by_user_id: str,
                 split_type: SplitType, currency: str = "USD"):
        """Initialize a new expense.
        
        Args:
            amount: Total amount of the expense
            description: Description of the expense
            paid_by_user_id: ID of user who paid for the expense
            split_type: How the expense should be split
            currency: Currency code (default: USD)
        """
        self.id = str(uuid.uuid4())
        self.amount = float(amount)
        self.description = description
        self.paid_by_user_id = paid_by_user_id
        self.split_type = split_type
        self.currency = currency
        self.created_at = datetime.now()
        
        # Split details - will be populated based on split_type
        self.user_shares: Dict[str, float] = {}  # user_id -> amount they owe
        
    def add_user_share(self, user_id: str, amount: float):
        """Add a user's share of this expense.
        
        Args:
            user_id: ID of the user
            amount: Amount this user owes for this expense
        """
        self.user_shares[user_id] = float(amount)
    
    def get_user_share(self, user_id: str) -> float:
        """Get a user's share of this expense.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Amount the user owes for this expense
        """
        return self.user_shares.get(user_id, 0.0)
    
    def validate_split(self) -> bool:
        """Validate that the split adds up to the total amount.
        
        Returns:
            True if the split is valid, False otherwise
        """
        total_split = sum(self.user_shares.values())
        # Allow for small floating point differences
        return abs(total_split - self.amount) < 0.01
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert expense to dictionary representation."""
        return {
            'id': self.id,
            'amount': self.amount,
            'description': self.description,
            'paid_by_user_id': self.paid_by_user_id,
            'split_type': self.split_type.value,
            'currency': self.currency,
            'created_at': self.created_at.isoformat(),
            'user_shares': self.user_shares
        }
    
    def __str__(self) -> str:
        return f"Expense({self.description}: {self.currency}{self.amount})"
    
    def __repr__(self) -> str:
        return f"Expense(id={self.id}, amount={self.amount}, description={self.description})"
