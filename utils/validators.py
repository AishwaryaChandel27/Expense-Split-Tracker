"""Validation utilities for expense tracking."""

from typing import Dict, List
from models.group import Group


class ExpenseValidator:
    """Validation utilities for expense operations."""
    
    @staticmethod
    def validate_amount(amount: float) -> None:
        """Validate expense amount.
        
        Args:
            amount: Amount to validate
            
        Raises:
            ValueError: If amount is invalid
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        if amount > 1000000:  # Reasonable upper limit
            raise ValueError("Amount too large")
    
    @staticmethod
    def validate_users_in_group(user_ids: List[str], group: Group) -> None:
        """Validate that all users are in the group.
        
        Args:
            user_ids: List of user IDs to validate
            group: Group to check against
            
        Raises:
            ValueError: If any user is not in the group
        """
        if not user_ids:
            raise ValueError("At least one user must be specified")
        
        for user_id in user_ids:
            if user_id not in group.users:
                raise ValueError(f"User {user_id} not found in group")
    
    @staticmethod
    def validate_exact_split(total_amount: float, user_amounts: Dict[str, float]) -> None:
        """Validate exact amount split.
        
        Args:
            total_amount: Total expense amount
            user_amounts: Dictionary of user_id -> amount
            
        Raises:
            ValueError: If split is invalid
        """
        if not user_amounts:
            raise ValueError("User amounts cannot be empty")
        
        # Check individual amounts
        for user_id, amount in user_amounts.items():
            if amount < 0:
                raise ValueError(f"Amount for user {user_id} cannot be negative")
        
        # Check total adds up
        split_total = sum(user_amounts.values())
        if abs(split_total - total_amount) > 0.01:
            raise ValueError(f"Split total {split_total} doesn't match expense amount {total_amount}")
    
    @staticmethod
    def validate_percentage_split(user_percentages: Dict[str, float]) -> None:
        """Validate percentage split.
        
        Args:
            user_percentages: Dictionary of user_id -> percentage
            
        Raises:
            ValueError: If percentages are invalid
        """
        if not user_percentages:
            raise ValueError("User percentages cannot be empty")
        
        # Check individual percentages
        for user_id, percentage in user_percentages.items():
            if percentage < 0 or percentage > 100:
                raise ValueError(f"Percentage for user {user_id} must be between 0 and 100")
        
        # Check total adds up to 100%
        total_percentage = sum(user_percentages.values())
        if abs(total_percentage - 100) > 0.01:
            raise ValueError(f"Percentages must add up to 100%, got {total_percentage}%")
    
    @staticmethod
    def validate_settlement_amount(amount: float, max_amount: float) -> None:
        """Validate settlement amount.
        
        Args:
            amount: Settlement amount
            max_amount: Maximum allowed settlement amount
            
        Raises:
            ValueError: If settlement amount is invalid
        """
        if amount <= 0:
            raise ValueError("Settlement amount must be positive")
        
        if amount > max_amount + 0.01:  # Allow small floating point differences
            raise ValueError(f"Settlement amount {amount} exceeds maximum {max_amount}")


class CurrencyValidator:
    """Validation utilities for currency operations."""
    
    SUPPORTED_CURRENCIES = {"USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "INR"}
    
    @staticmethod
    def validate_currency(currency: str) -> None:
        """Validate currency code.
        
        Args:
            currency: Currency code to validate
            
        Raises:
            ValueError: If currency is invalid
        """
        if not currency or len(currency) != 3:
            raise ValueError("Currency must be a 3-character code")
        
        currency = currency.upper()
        if currency not in CurrencyValidator.SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency {currency}")
    
    @staticmethod
    def validate_currency_compatibility(currency1: str, currency2: str) -> None:
        """Validate that two currencies are compatible.
        
        Args:
            currency1: First currency
            currency2: Second currency
            
        Raises:
            ValueError: If currencies are not compatible
        """
        CurrencyValidator.validate_currency(currency1)
        CurrencyValidator.validate_currency(currency2)
        
        if currency1.upper() != currency2.upper():
            raise ValueError(f"Currency mismatch: {currency1} vs {currency2}")
