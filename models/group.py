"""Group model for managing expense sharing groups."""

from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
from .user import User
from .expense import Expense


class Group:
    """Represents a group of users sharing expenses."""
    
    def __init__(self, name: str, description: str = "", currency: str = "USD"):
        """Initialize a new group.
        
        Args:
            name: Name of the group
            description: Optional description
            currency: Default currency for the group
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.currency = currency
        self.created_at = datetime.now()
        
        # Store users and expenses
        self.users: Dict[str, User] = {}  # user_id -> User
        self.expenses: Dict[str, Expense] = {}  # expense_id -> Expense
        
        # Track user balances: positive = owed by user, negative = owed to user
        self.balances: Dict[str, float] = {}  # user_id -> balance
    
    def add_user(self, user: User) -> bool:
        """Add a user to the group.
        
        Args:
            user: User to add
            
        Returns:
            True if user was added, False if already exists
        """
        if user.id in self.users:
            return False
        
        self.users[user.id] = user
        self.balances[user.id] = 0.0
        return True
    
    def remove_user(self, user_id: str) -> bool:
        """Remove a user from the group.
        
        Args:
            user_id: ID of user to remove
            
        Returns:
            True if user was removed, False if not found
        """
        if user_id not in self.users:
            return False
        
        # Check if user has any outstanding balance
        if abs(self.balances.get(user_id, 0)) > 0.01:
            raise ValueError("Cannot remove user with outstanding balance")
        
        del self.users[user_id]
        del self.balances[user_id]
        return True
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID.
        
        Args:
            user_id: ID of the user
            
        Returns:
            User object or None if not found
        """
        return self.users.get(user_id)
    
    def get_user_by_name(self, name: str) -> Optional[User]:
        """Get a user by name.
        
        Args:
            name: Name of the user
            
        Returns:
            User object or None if not found
        """
        for user in self.users.values():
            if user.name == name:
                return user
        return None
    
    def add_expense(self, expense: Expense) -> bool:
        """Add an expense to the group.
        
        Args:
            expense: Expense to add
            
        Returns:
            True if expense was added, False otherwise
        """
        # Validate that the paying user is in the group
        if expense.paid_by_user_id not in self.users:
            raise ValueError("Paying user not in group")
        
        # Validate currency compatibility
        if expense.currency != self.currency:
            raise ValueError(f"Expense currency {expense.currency} doesn't match group currency {self.currency}")
        
        # Validate that all users in the split are in the group
        for user_id in expense.user_shares.keys():
            if user_id not in self.users:
                raise ValueError(f"User {user_id} in expense split not in group")
        
        # Validate the split adds up correctly
        if not expense.validate_split():
            raise ValueError("Expense split doesn't add up to total amount")
        
        self.expenses[expense.id] = expense
        self._update_balances_for_expense(expense)
        return True
    
    def _update_balances_for_expense(self, expense: Expense):
        """Update user balances based on a new expense.
        
        Args:
            expense: The expense to process
        """
        # The person who paid gets credited (negative balance)
        self.balances[expense.paid_by_user_id] -= expense.amount
        
        # Each person who owes money gets debited (positive balance)
        for user_id, amount in expense.user_shares.items():
            self.balances[user_id] += amount
    
    def get_user_balance(self, user_id: str) -> float:
        """Get a user's current balance.
        
        Args:
            user_id: ID of the user
            
        Returns:
            User's balance (positive = owes money, negative = owed money)
        """
        return self.balances.get(user_id, 0.0)
    
    def get_all_balances(self) -> Dict[str, float]:
        """Get all user balances.
        
        Returns:
            Dictionary of user_id -> balance
        """
        return self.balances.copy()
    
    def settle_debt(self, payer_id: str, payee_id: str, amount: float) -> bool:
        """Settle debt between two users.
        
        Args:
            payer_id: ID of user paying
            payee_id: ID of user receiving payment
            amount: Amount being paid
            
        Returns:
            True if settlement was successful
        """
        if payer_id not in self.users or payee_id not in self.users:
            raise ValueError("Both users must be in the group")
        
        if amount <= 0:
            raise ValueError("Settlement amount must be positive")
        
        payer_balance = self.balances[payer_id]
        payee_balance = self.balances[payee_id]
        
        # Validate that payer owes money and payee is owed money
        if payer_balance <= 0:
            raise ValueError("Payer doesn't owe any money")
        
        if payee_balance >= 0:
            raise ValueError("Payee is not owed any money")
        
        # Validate that payment doesn't exceed what's owed
        max_payment = min(payer_balance, abs(payee_balance))
        if amount > max_payment + 0.01:  # Allow small floating point differences
            raise ValueError(f"Payment amount {amount} exceeds maximum payable {max_payment}")
        
        # Update balances
        self.balances[payer_id] -= amount
        self.balances[payee_id] += amount
        
        return True
    
    def get_expenses(self) -> List[Expense]:
        """Get all expenses in the group.
        
        Returns:
            List of expenses ordered by creation date
        """
        return sorted(self.expenses.values(), key=lambda e: e.created_at, reverse=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert group to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'currency': self.currency,
            'created_at': self.created_at.isoformat(),
            'users': [user.to_dict() for user in self.users.values()],
            'expenses': [expense.to_dict() for expense in self.expenses.values()],
            'balances': self.balances
        }
    
    def __str__(self) -> str:
        return f"Group({self.name})"
    
    def __repr__(self) -> str:
        return f"Group(id={self.id}, name={self.name}, users={len(self.users)})"
