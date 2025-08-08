"""Main expense tracking service that coordinates all operations."""

from typing import Dict, List, Optional, Tuple, Any
from models.group import Group
from models.user import User
from models.expense import Expense, SplitType
from services.debt_simplifier import DebtSimplifier
from utils.validators import ExpenseValidator


class ExpenseTracker:
    """Main service for managing expense tracking across multiple groups."""
    
    def __init__(self):
        """Initialize the expense tracker."""
        self.groups: Dict[str, Group] = {}
    
    def create_group(self, name: str, description: str = "", currency: str = "USD") -> Group:
        """Create a new expense group.
        
        Args:
            name: Name of the group
            description: Optional description
            currency: Currency for the group
            
        Returns:
            Created group
        """
        group = Group(name, description, currency)
        self.groups[group.id] = group
        return group
    
    def get_group(self, group_id: str) -> Optional[Group]:
        """Get a group by ID.
        
        Args:
            group_id: ID of the group
            
        Returns:
            Group object or None if not found
        """
        return self.groups.get(group_id)
    
    def get_all_groups(self) -> List[Group]:
        """Get all groups.
        
        Returns:
            List of all groups
        """
        return list(self.groups.values())
    
    def delete_group(self, group_id: str) -> bool:
        """Delete a group.
        
        Args:
            group_id: ID of the group to delete
            
        Returns:
            True if group was deleted, False if not found
        """
        if group_id not in self.groups:
            return False
        
        # Check if group has any outstanding balances
        group = self.groups[group_id]
        for balance in group.balances.values():
            if abs(balance) > 0.01:
                raise ValueError("Cannot delete group with outstanding balances")
        
        del self.groups[group_id]
        return True
    
    def add_user_to_group(self, group_id: str, name: str, email: Optional[str] = None) -> User:
        """Add a new user to a group.
        
        Args:
            group_id: ID of the group
            name: Name of the user
            email: Optional email
            
        Returns:
            Created user
            
        Raises:
            ValueError: If group not found or user already exists
        """
        group = self.get_group(group_id)
        if not group:
            raise ValueError("Group not found")
        
        # Check if user with same name already exists
        if group.get_user_by_name(name):
            raise ValueError("User with this name already exists in the group")
        
        user = User(name, email)
        group.add_user(user)
        return user
    
    def add_expense_equal_split(self, group_id: str, amount: float, description: str,
                               paid_by_user_id: str, user_ids: List[str]) -> Expense:
        """Add an expense with equal split.
        
        Args:
            group_id: ID of the group
            amount: Total amount of expense
            description: Description of expense
            paid_by_user_id: ID of user who paid
            user_ids: List of user IDs to split among
            
        Returns:
            Created expense
        """
        group = self.get_group(group_id)
        if not group:
            raise ValueError("Group not found")
        
        # Validate inputs
        ExpenseValidator.validate_amount(amount)
        ExpenseValidator.validate_users_in_group(user_ids, group)
        
        # Create expense
        expense = Expense(amount, description, paid_by_user_id, SplitType.EQUAL, group.currency)
        
        # Calculate equal split
        split_amount = amount / len(user_ids)
        for user_id in user_ids:
            expense.add_user_share(user_id, split_amount)
        
        group.add_expense(expense)
        return expense
    
    def add_expense_exact_split(self, group_id: str, amount: float, description: str,
                               paid_by_user_id: str, user_amounts: Dict[str, float]) -> Expense:
        """Add an expense with exact amount split.
        
        Args:
            group_id: ID of the group
            amount: Total amount of expense
            description: Description of expense
            paid_by_user_id: ID of user who paid
            user_amounts: Dictionary of user_id -> exact amount they owe
            
        Returns:
            Created expense
        """
        group = self.get_group(group_id)
        if not group:
            raise ValueError("Group not found")
        
        # Validate inputs
        ExpenseValidator.validate_amount(amount)
        ExpenseValidator.validate_users_in_group(list(user_amounts.keys()), group)
        ExpenseValidator.validate_exact_split(amount, user_amounts)
        
        # Create expense
        expense = Expense(amount, description, paid_by_user_id, SplitType.EXACT, group.currency)
        
        # Add exact amounts
        for user_id, user_amount in user_amounts.items():
            expense.add_user_share(user_id, user_amount)
        
        group.add_expense(expense)
        return expense
    
    def add_expense_percentage_split(self, group_id: str, amount: float, description: str,
                                   paid_by_user_id: str, user_percentages: Dict[str, float]) -> Expense:
        """Add an expense with percentage split.
        
        Args:
            group_id: ID of the group
            amount: Total amount of expense
            description: Description of expense
            paid_by_user_id: ID of user who paid
            user_percentages: Dictionary of user_id -> percentage (0-100)
            
        Returns:
            Created expense
        """
        group = self.get_group(group_id)
        if not group:
            raise ValueError("Group not found")
        
        # Validate inputs
        ExpenseValidator.validate_amount(amount)
        ExpenseValidator.validate_users_in_group(list(user_percentages.keys()), group)
        ExpenseValidator.validate_percentage_split(user_percentages)
        
        # Create expense
        expense = Expense(amount, description, paid_by_user_id, SplitType.PERCENTAGE, group.currency)
        
        # Calculate amounts from percentages
        for user_id, percentage in user_percentages.items():
            user_amount = amount * (percentage / 100)
            expense.add_user_share(user_id, user_amount)
        
        group.add_expense(expense)
        return expense
    
    def settle_debt(self, group_id: str, payer_id: str, payee_id: str, amount: float) -> bool:
        """Settle debt between two users in a group.
        
        Args:
            group_id: ID of the group
            payer_id: ID of user paying
            payee_id: ID of user receiving payment
            amount: Amount being paid
            
        Returns:
            True if settlement was successful
        """
        group = self.get_group(group_id)
        if not group:
            raise ValueError("Group not found")
        
        return group.settle_debt(payer_id, payee_id, amount)
    
    def get_group_balances(self, group_id: str) -> Dict[str, float]:
        """Get all user balances for a group.
        
        Args:
            group_id: ID of the group
            
        Returns:
            Dictionary of user_id -> balance
        """
        group = self.get_group(group_id)
        if not group:
            raise ValueError("Group not found")
        
        return group.get_all_balances()
    
    def get_simplified_debts(self, group_id: str) -> List[Tuple[str, str, float]]:
        """Get simplified debt transactions for a group.
        
        Args:
            group_id: ID of the group
            
        Returns:
            List of tuples (payer_id, payee_id, amount)
        """
        group = self.get_group(group_id)
        if not group:
            raise ValueError("Group not found")
        
        return DebtSimplifier.simplify_debts(group.get_all_balances())
    
    def get_user_debt_summary(self, group_id: str, user_id: str) -> Dict[str, Any]:
        """Get debt summary for a specific user in a group.
        
        Args:
            group_id: ID of the group
            user_id: ID of the user
            
        Returns:
            Dictionary with user's debt summary
        """
        group = self.get_group(group_id)
        if not group:
            raise ValueError("Group not found")
        
        if user_id not in group.users:
            raise ValueError("User not found in group")
        
        return DebtSimplifier.get_user_debt_summary(user_id, group.get_all_balances())
    
    def get_group_summary(self, group_id: str) -> Dict[str, Any]:
        """Get a comprehensive summary of a group.
        
        Args:
            group_id: ID of the group
            
        Returns:
            Dictionary with group summary including users, expenses, and simplified debts
        """
        group = self.get_group(group_id)
        if not group:
            raise ValueError("Group not found")
        
        simplified_debts = self.get_simplified_debts(group_id)
        
        return {
            'group': group.to_dict(),
            'simplified_debts': simplified_debts,
            'total_expenses': sum(expense.amount for expense in group.expenses.values()),
            'expense_count': len(group.expenses),
            'user_count': len(group.users)
        }
