"""Comprehensive tests for the complete expense split tracker functionality."""

import unittest
import sys
import os

# Add the parent directory to the path to import the application modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.expense_tracker import ExpenseTracker
from models.expense import SplitType
from services.debt_simplifier import DebtSimplifier


class TestCompleteApplicationFunctionality(unittest.TestCase):
    """Test all major functionality of the expense split tracker."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.tracker = ExpenseTracker()
        
        # Create test group and users
        self.group = self.tracker.create_group("Test Group", "Test Description", "USD")
        self.user1 = self.tracker.add_user_to_group(self.group.id, "Alice", "alice@test.com")
        self.user2 = self.tracker.add_user_to_group(self.group.id, "Bob", "bob@test.com")
        self.user3 = self.tracker.add_user_to_group(self.group.id, "Carol", "carol@test.com")
    
    def test_group_creation_and_management(self):
        """Test group creation and basic management."""
        # Test group creation
        self.assertEqual(self.group.name, "Test Group")
        self.assertEqual(self.group.description, "Test Description")
        self.assertEqual(self.group.currency, "USD")
        
        # Test getting all groups
        groups = self.tracker.get_all_groups()
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].name, "Test Group")
        
        # Test getting specific group
        retrieved_group = self.tracker.get_group(self.group.id)
        self.assertIsNotNone(retrieved_group)
        if retrieved_group:
            self.assertEqual(retrieved_group.name, "Test Group")
    
    def test_user_management(self):
        """Test user addition and management."""
        # Test users were added correctly
        self.assertEqual(len(self.group.users), 3)
        
        # Test user details
        users = list(self.group.users.values())
        user_names = [user.name for user in users]
        self.assertIn("Alice", user_names)
        self.assertIn("Bob", user_names)
        self.assertIn("Carol", user_names)
    
    def test_equal_split_functionality(self):
        """Test equal split expense functionality."""
        # Add equal split expense
        expense = self.tracker.add_expense_equal_split(
            self.group.id, 300.0, "Hotel Booking",
            self.user1.id, [self.user1.id, self.user2.id, self.user3.id]
        )
        
        # Verify expense creation
        self.assertEqual(expense.amount, 300.0)
        self.assertEqual(expense.description, "Hotel Booking")
        self.assertEqual(expense.split_type, SplitType.EQUAL)
        
        # Verify equal split calculation
        self.assertEqual(len(expense.user_shares), 3)
        for user_id, amount in expense.user_shares.items():
            self.assertEqual(amount, 100.0)  # 300 / 3 = 100
        
        # Verify balances (automatically updated when expense is added)
        self.assertEqual(self.group.balances[self.user1.id], -200.0)  # Paid 300, owes 100
        self.assertEqual(self.group.balances[self.user2.id], 100.0)   # Owes 100
        self.assertEqual(self.group.balances[self.user3.id], 100.0)   # Owes 100
    
    def test_exact_split_functionality(self):
        """Test exact amount split functionality."""
        # Add exact split expense
        user_amounts = {
            self.user1.id: 50.0,
            self.user2.id: 60.0,
            self.user3.id: 40.0
        }
        expense = self.tracker.add_expense_exact_split(
            self.group.id, 150.0, "Gas and Tolls",
            self.user2.id, user_amounts
        )
        
        # Verify expense creation
        self.assertEqual(expense.amount, 150.0)
        self.assertEqual(expense.split_type, SplitType.EXACT)
        
        # Verify exact amounts
        self.assertEqual(expense.user_shares[self.user1.id], 50.0)
        self.assertEqual(expense.user_shares[self.user2.id], 60.0)
        self.assertEqual(expense.user_shares[self.user3.id], 40.0)
        
        # Verify balances (automatically updated when expense is added)
        self.assertEqual(self.group.balances[self.user1.id], 50.0)    # Owes 50
        self.assertEqual(self.group.balances[self.user2.id], -90.0)   # Paid 150, owes 60
        self.assertEqual(self.group.balances[self.user3.id], 40.0)    # Owes 40
    
    def test_percentage_split_functionality(self):
        """Test percentage split functionality."""
        # Add percentage split expense
        user_percentages = {
            self.user1.id: 40.0,  # 40%
            self.user2.id: 35.0,  # 35%
            self.user3.id: 25.0   # 25%
        }
        expense = self.tracker.add_expense_percentage_split(
            self.group.id, 240.0, "Restaurant Dinner",
            self.user3.id, user_percentages
        )
        
        # Verify expense creation
        self.assertEqual(expense.amount, 240.0)
        self.assertEqual(expense.split_type, SplitType.PERCENTAGE)
        
        # Verify percentage calculations
        self.assertEqual(expense.user_shares[self.user1.id], 96.0)   # 40% of 240
        self.assertEqual(expense.user_shares[self.user2.id], 84.0)   # 35% of 240
        self.assertEqual(expense.user_shares[self.user3.id], 60.0)   # 25% of 240
        
        # Verify balances (automatically updated when expense is added)
        self.assertEqual(self.group.balances[self.user1.id], 96.0)    # Owes 96
        self.assertEqual(self.group.balances[self.user2.id], 84.0)    # Owes 84
        self.assertEqual(self.group.balances[self.user3.id], -180.0)  # Paid 240, owes 60
    
    def test_complex_scenario_with_debt_simplification(self):
        """Test complex scenario with multiple expenses and debt simplification."""
        # Add multiple expenses
        self.tracker.add_expense_equal_split(
            self.group.id, 300.0, "Hotel",
            self.user1.id, [self.user1.id, self.user2.id, self.user3.id]
        )
        
        self.tracker.add_expense_exact_split(
            self.group.id, 150.0, "Gas",
            self.user2.id, {self.user1.id: 50.0, self.user2.id: 60.0, self.user3.id: 40.0}
        )
        
        self.tracker.add_expense_percentage_split(
            self.group.id, 240.0, "Dinner",
            self.user3.id, {self.user1.id: 40.0, self.user2.id: 35.0, self.user3.id: 25.0}
        )
        
        # Get simplified debts
        simplified_debts = self.tracker.get_simplified_debts(self.group.id)
        
        # Verify debt simplification worked
        self.assertIsInstance(simplified_debts, list)
        
        # Test that total debt amount is preserved
        total_debt_before = sum(abs(balance) for balance in self.group.balances.values()) / 2
        total_debt_after = sum(debt[2] for debt in simplified_debts)  # Amount is third element in tuple
        self.assertAlmostEqual(total_debt_before, total_debt_after, places=2)
    
    def test_debt_settlement(self):
        """Test debt settlement functionality."""
        # Add an expense to create debt
        self.tracker.add_expense_equal_split(
            self.group.id, 300.0, "Hotel",
            self.user1.id, [self.user1.id, self.user2.id, self.user3.id]
        )
        
        # Settle debt
        success = self.tracker.settle_debt(
            self.group.id, self.user2.id, self.user1.id, 100.0
        )
        
        # Verify settlement
        self.assertTrue(success)
        self.assertEqual(self.group.balances[self.user1.id], -100.0)  # Alice gets payment from Bob (-200 + 100)
        self.assertEqual(self.group.balances[self.user2.id], 0.0)     # Bob settled debt (100 - 100)
        self.assertEqual(self.group.balances[self.user3.id], 100.0)   # Carol still owes 100
    
    def test_error_handling(self):
        """Test error handling for invalid operations."""
        # Test invalid group ID
        with self.assertRaises(ValueError):
            self.tracker.add_expense_equal_split(
                "invalid-id", 100.0, "Test",
                self.user1.id, [self.user1.id]
            )
        
        # Test invalid amount
        with self.assertRaises(ValueError):
            self.tracker.add_expense_equal_split(
                self.group.id, -100.0, "Test",
                self.user1.id, [self.user1.id]
            )
        
        # Test invalid user in split
        with self.assertRaises(ValueError):
            self.tracker.add_expense_equal_split(
                self.group.id, 100.0, "Test",
                self.user1.id, ["invalid-user-id"]
            )
        
        # Test invalid exact split (amounts don't match total)
        with self.assertRaises(ValueError):
            self.tracker.add_expense_exact_split(
                self.group.id, 100.0, "Test",
                self.user1.id, {self.user1.id: 50.0, self.user2.id: 60.0}  # Total 110, not 100
            )
        
        # Test invalid percentage split (doesn't sum to 100)
        with self.assertRaises(ValueError):
            self.tracker.add_expense_percentage_split(
                self.group.id, 100.0, "Test",
                self.user1.id, {self.user1.id: 60.0, self.user2.id: 50.0}  # Total 110%, not 100%
            )


if __name__ == '__main__':
    unittest.main()