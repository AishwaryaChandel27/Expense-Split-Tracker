"""Debt simplification service to minimize transactions."""

from typing import Dict, List, Tuple, Set, Any
from collections import defaultdict
import heapq


class DebtSimplifier:
    """Service to simplify debts by minimizing the number of transactions."""
    
    @staticmethod
    def simplify_debts(balances: Dict[str, float]) -> List[Tuple[str, str, float]]:
        """Simplify debts to minimize number of transactions.
        
        This algorithm finds the minimum number of transactions needed to settle
        all debts by matching creditors with debtors optimally.
        
        Args:
            balances: Dictionary of user_id -> balance 
                     (positive = owes money, negative = owed money)
        
        Returns:
            List of tuples (payer_id, payee_id, amount) representing simplified transactions
        """
        # Filter out zero balances and create separate lists for debtors and creditors
        debtors = []  # People who owe money (positive balance)
        creditors = []  # People who are owed money (negative balance)
        
        for user_id, balance in balances.items():
            if balance > 0.01:  # Owes money
                heapq.heappush(debtors, (-balance, user_id))  # Use negative for max heap
            elif balance < -0.01:  # Owed money
                heapq.heappush(creditors, (balance, user_id))  # Min heap for most owed
        
        transactions = []
        
        # Process debts by matching largest debtor with largest creditor
        while debtors and creditors:
            # Get the person who owes the most money
            debt_amount, debtor_id = heapq.heappop(debtors)
            debt_amount = -debt_amount  # Convert back to positive
            
            # Get the person who is owed the most money
            credit_amount, creditor_id = heapq.heappop(creditors)
            credit_amount = -credit_amount  # Convert to positive (amount owed to them)
            
            # Calculate how much can be settled
            settlement_amount = min(debt_amount, credit_amount)
            
            # Add transaction
            transactions.append((debtor_id, creditor_id, settlement_amount))
            
            # Update remaining balances
            remaining_debt = debt_amount - settlement_amount
            remaining_credit = credit_amount - settlement_amount
            
            # Put back any remaining balances
            if remaining_debt > 0.01:
                heapq.heappush(debtors, (-remaining_debt, debtor_id))
            
            if remaining_credit > 0.01:
                heapq.heappush(creditors, (-remaining_credit, creditor_id))
        
        return transactions
    
    @staticmethod
    def calculate_debt_graph(balances: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        """Calculate who owes how much to whom after simplification.
        
        Args:
            balances: Dictionary of user_id -> balance
        
        Returns:
            Nested dictionary: debtor_id -> {creditor_id: amount}
        """
        simplified_transactions = DebtSimplifier.simplify_debts(balances)
        
        debt_graph = defaultdict(dict)
        for payer_id, payee_id, amount in simplified_transactions:
            debt_graph[payer_id][payee_id] = amount
        
        return dict(debt_graph)
    
    @staticmethod
    def get_user_debt_summary(user_id: str, balances: Dict[str, float]) -> Dict[str, Any]:
        """Get a summary of what a specific user owes and is owed.
        
        Args:
            user_id: ID of the user
            balances: Dictionary of user_id -> balance
        
        Returns:
            Dictionary with debt summary for the user
        """
        debt_graph = DebtSimplifier.calculate_debt_graph(balances)
        
        # What this user owes to others
        owes_to = debt_graph.get(user_id, {})
        
        # What others owe to this user
        owed_by = {}
        for debtor_id, creditors in debt_graph.items():
            if user_id in creditors:
                owed_by[debtor_id] = creditors[user_id]
        
        total_owes = sum(owes_to.values())
        total_owed = sum(owed_by.values())
        net_balance = total_owes - total_owed
        
        return {
            'user_id': user_id,
            'owes_to': owes_to,
            'owed_by': owed_by,
            'total_owes': total_owes,
            'total_owed': total_owed,
            'net_balance': net_balance
        }
    
    @staticmethod
    def validate_simplification(original_balances: Dict[str, float], 
                              transactions: List[Tuple[str, str, float]]) -> bool:
        """Validate that the simplified transactions preserve the original balances.
        
        Args:
            original_balances: Original user balances
            transactions: List of simplified transactions
        
        Returns:
            True if simplification is valid, False otherwise
        """
        # Calculate final balances after applying transactions
        final_balances = original_balances.copy()
        
        for payer_id, payee_id, amount in transactions:
            final_balances[payer_id] -= amount
            final_balances[payee_id] += amount
        
        # Check that all balances are approximately zero
        for balance in final_balances.values():
            if abs(balance) > 0.01:
                return False
        
        return True
