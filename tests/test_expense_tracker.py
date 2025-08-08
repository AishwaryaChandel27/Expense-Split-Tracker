"""Tests for ExpenseTracker service."""

import unittest
from services.expense_tracker import ExpenseTracker
from models.expense import SplitType


class TestExpenseTracker(unittest.TestCase):
    """Test cases for ExpenseTracker service."""
    
    def setUp(self):
        """Set up test data."""
        self.tracker = ExpenseTracker()
        self.group = self.tracker.create_group("Trip to Paris")
        self.user1 = self.tracker.add_user_to_group(self.group.id, "Alice")
        self.user2 = self.tracker.add_user_to_group(self.group.id, "Bob")
        self.user3 = self.tracker.add_user_to_group(self.group.id, "Charlie")
    
    def test_equal_split(self):
        """Test equal split of expense."""
        expense = self.tracker.add_expense_equal_split(
            self.group.id, 90.0, "Dinner", self.user1.id, 
            [self.user1.id, self.user2.id, self.user3.id]
        )
        
        # Each user should owe $30
        self.assertEqual(expense.get_user_share(self.user1.id), 30.0)
        self.assertEqual(expense.get_user_share(self.user2.id), 30.0)
        self.assertEqual(expense.get_user_share(self.user3.id), 30.0)
        
        # Check balances
        balances = self.tracker.get_group_balances(self.group.id)
        self.assertEqual(balances[self.user1.id], -60.0)  # Paid 90, owes 30
        self.assertEqual(balances[self.user2.id], 30.0)   # Owes 30
        self.assertEqual(balances[self.user3.id], 30.0)   # Owes 30
    
    def test_exact_amount_split(self):
        """Test exact amount split."""
        expense = self.tracker.add_expense_exact_split(
            self.group.id, 100.0, "Groceries", self.user1.id,
            {self.user1.id: 70.0, self.user2.id: 30.0}
        )
        
        self.assertEqual(expense.get_user_share(self.user1.id), 70.0)
        self.assertEqual(expense.get_user_share(self.user2.id), 30.0)
        
        # Check balances
        balances = self.tracker.get_group_balances(self.group.id)
        self.assertEqual(balances[self.user1.id], -30.0)  # Paid 100, owes 70
        self.assertEqual(balances[self.user2.id], 30.0)   # Owes 30
    
    def test_percentage_split(self):
        """Test percentage split."""
        expense = self.tracker.add_expense_percentage_split(
            self.group.id, 200.0, "Shopping", self.user1.id,
            {self.user1.id: 60.0, self.user2.id: 40.0}
        )
        
        self.assertEqual(expense.get_user_share(self.user1.id), 120.0)
        self.assertEqual(expense.get_user_share(self.user2.id), 80.0)
        
        # Check balances
        balances = self.tracker.get_group_balances(self.group.id)
        self.assertEqual(balances[self.user1.id], -80.0)  # Paid 200, owes 120
        self.assertEqual(balances[self.user2.id], 80.0)   # Owes 80
    
    def test_settling_debt(self):
        """Test settling debt."""
        # Add expense
        self.tracker.add_expense_equal_split(
            self.group.id, 60.0, "Lunch", self.user1.id,
            [self.user1.id, self.user2.id]
        )
        
        # user1: -30 (paid 60, owes 30), user2: 30 (owes 30)
        
        # Settle debt
        self.assertTrue(self.tracker.settle_debt(
            self.group.id, self.user2.id, self.user1.id, 30.0
        ))
        
        # Check final balances
        balances = self.tracker.get_group_balances(self.group.id)
        self.assertEqual(balances[self.user1.id], 0.0)
        self.assertEqual(balances[self.user2.id], 0.0)
    
    def test_simplify_debts(self):
        """Test debt simplification."""
        # Create complex debt scenario
        # user1 pays for expense1 (60), split between user1 and user2
        self.tracker.add_expense_exact_split(
            self.group.id, 60.0, "Expense1", self.user1.id,
            {self.user1.id: 30.0, self.user2.id: 30.0}
        )
        
        # user2 pays for expense2 (40), split between user2 and user3
        self.tracker.add_expense_exact_split(
            self.group.id, 40.0, "Expense2", self.user2.id,
            {self.user2.id: 20.0, self.user3.id: 20.0}
        )
        
        # Current balances:
        # user1: -30 (paid 60, owes 30)
        # user2: 10 (paid 40, owes 50 total)
        # user3: 20 (owes 20)
        
        simplified_debts = self.tracker.get_simplified_debts(self.group.id)
        
        # Should have fewer transactions than direct settlements
        self.assertLessEqual(len(simplified_debts), 2)
        
        # Verify total amounts balance
        total_payments = sum(amount for _, _, amount in simplified_debts)
        self.assertAlmostEqual(total_payments, 30.0, places=2)  # Total debt to settle
    
    def test_group_summary(self):
        """Test group summary generation."""
        # Add some expenses
        self.tracker.add_expense_equal_split(
            self.group.id, 90.0, "Dinner", self.user1.id,
            [self.user1.id, self.user2.id, self.user3.id]
        )
        
        self.tracker.add_expense_exact_split(
            self.group.id, 50.0, "Taxi", self.user2.id,
            {self.user2.id: 20.0, self.user3.id: 30.0}
        )
        
        summary = self.tracker.get_group_summary(self.group.id)
        
        self.assertEqual(summary['expense_count'], 2)
        self.assertEqual(summary['user_count'], 3)
        self.assertEqual(summary['total_expenses'], 140.0)
        self.assertIn('simplified_debts', summary)
        self.assertIn('group', summary)
    
    def test_invalid_operations(self):
        """Test error handling for invalid operations."""
        # Invalid group ID
        with self.assertRaises(ValueError):
            self.tracker.add_expense_equal_split(
                "invalid_id", 100.0, "Test", self.user1.id, [self.user1.id]
            )
        
        # Invalid user in split
        with self.assertRaises(ValueError):
            self.tracker.add_expense_equal_split(
                self.group.id, 100.0, "Test", self.user1.id, ["invalid_user"]
            )
        
        # Invalid exact split (doesn't add up)
        with self.assertRaises(ValueError):
            self.tracker.add_expense_exact_split(
                self.group.id, 100.0, "Test", self.user1.id,
                {self.user1.id: 50.0, self.user2.id: 30.0}  # Only adds to 80
            )
        
        # Invalid percentage split
        with self.assertRaises(ValueError):
            self.tracker.add_expense_percentage_split(
                self.group.id, 100.0, "Test", self.user1.id,
                {self.user1.id: 60.0, self.user2.id: 50.0}  # Adds to 110%
            )


if __name__ == '__main__':
    unittest.main()
