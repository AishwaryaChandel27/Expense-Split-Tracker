"""Tests for model classes."""

import unittest
from datetime import datetime
from models.user import User
from models.expense import Expense, SplitType
from models.group import Group


class TestUser(unittest.TestCase):
    """Test cases for User model."""
    
    def test_user_creation(self):
        """Test user creation."""
        user = User("John Doe", "john@example.com")
        
        self.assertEqual(user.name, "John Doe")
        self.assertEqual(user.email, "john@example.com")
        self.assertIsNotNone(user.id)
    
    def test_user_equality(self):
        """Test user equality comparison."""
        user1 = User("John", "john@example.com")
        user2 = User("Jane", "jane@example.com")
        user3 = User("Bob", "bob@example.com")
        user3.id = user1.id  # Same ID
        
        self.assertNotEqual(user1, user2)
        self.assertEqual(user1, user3)
    
    def test_user_to_dict(self):
        """Test user dictionary conversion."""
        user = User("John Doe", "john@example.com")
        user_dict = user.to_dict()
        
        self.assertEqual(user_dict['name'], "John Doe")
        self.assertEqual(user_dict['email'], "john@example.com")
        self.assertEqual(user_dict['id'], user.id)


class TestExpense(unittest.TestCase):
    """Test cases for Expense model."""
    
    def test_expense_creation(self):
        """Test expense creation."""
        expense = Expense(100.0, "Dinner", "user1", SplitType.EQUAL)
        
        self.assertEqual(expense.amount, 100.0)
        self.assertEqual(expense.description, "Dinner")
        self.assertEqual(expense.paid_by_user_id, "user1")
        self.assertEqual(expense.split_type, SplitType.EQUAL)
        self.assertEqual(expense.currency, "USD")
    
    def test_add_user_share(self):
        """Test adding user shares."""
        expense = Expense(90.0, "Lunch", "user1", SplitType.EQUAL)
        
        expense.add_user_share("user1", 30.0)
        expense.add_user_share("user2", 30.0)
        expense.add_user_share("user3", 30.0)
        
        self.assertEqual(expense.get_user_share("user1"), 30.0)
        self.assertEqual(expense.get_user_share("user2"), 30.0)
        self.assertEqual(expense.get_user_share("user3"), 30.0)
    
    def test_validate_split(self):
        """Test expense split validation."""
        expense = Expense(100.0, "Test", "user1", SplitType.EXACT)
        
        # Invalid split
        expense.add_user_share("user1", 60.0)
        expense.add_user_share("user2", 30.0)
        self.assertFalse(expense.validate_split())
        
        # Valid split
        expense.add_user_share("user3", 10.0)
        self.assertTrue(expense.validate_split())


class TestGroup(unittest.TestCase):
    """Test cases for Group model."""
    
    def setUp(self):
        """Set up test data."""
        self.group = Group("Test Group", "A test group")
        self.user1 = User("Alice", "alice@example.com")
        self.user2 = User("Bob", "bob@example.com")
        self.user3 = User("Charlie", "charlie@example.com")
    
    def test_group_creation(self):
        """Test group creation."""
        self.assertEqual(self.group.name, "Test Group")
        self.assertEqual(self.group.description, "A test group")
        self.assertEqual(self.group.currency, "USD")
        self.assertEqual(len(self.group.users), 0)
    
    def test_add_user(self):
        """Test adding users to group."""
        self.assertTrue(self.group.add_user(self.user1))
        self.assertFalse(self.group.add_user(self.user1))  # Already exists
        
        self.assertEqual(len(self.group.users), 1)
        self.assertEqual(self.group.balances[self.user1.id], 0.0)
    
    def test_add_expense_equal_split(self):
        """Test adding expense with equal split."""
        # Add users
        self.group.add_user(self.user1)
        self.group.add_user(self.user2)
        self.group.add_user(self.user3)
        
        # Create expense
        expense = Expense(90.0, "Dinner", self.user1.id, SplitType.EQUAL)
        expense.add_user_share(self.user1.id, 30.0)
        expense.add_user_share(self.user2.id, 30.0)
        expense.add_user_share(self.user3.id, 30.0)
        
        # Add to group
        self.group.add_expense(expense)
        
        # Check balances
        self.assertEqual(self.group.get_user_balance(self.user1.id), -60.0)  # Paid 90, owes 30
        self.assertEqual(self.group.get_user_balance(self.user2.id), 30.0)   # Owes 30
        self.assertEqual(self.group.get_user_balance(self.user3.id), 30.0)   # Owes 30
    
    def test_settle_debt(self):
        """Test debt settlement."""
        # Set up users and expense
        self.group.add_user(self.user1)
        self.group.add_user(self.user2)
        
        expense = Expense(100.0, "Test", self.user1.id, SplitType.EQUAL)
        expense.add_user_share(self.user1.id, 50.0)
        expense.add_user_share(self.user2.id, 50.0)
        self.group.add_expense(expense)
        
        # user1 balance: -50 (paid 100, owes 50)
        # user2 balance: 50 (owes 50)
        
        # Settle debt
        self.assertTrue(self.group.settle_debt(self.user2.id, self.user1.id, 50.0))
        
        # Check final balances
        self.assertEqual(self.group.get_user_balance(self.user1.id), 0.0)
        self.assertEqual(self.group.get_user_balance(self.user2.id), 0.0)
    
    def test_settle_debt_validation(self):
        """Test debt settlement validation."""
        self.group.add_user(self.user1)
        self.group.add_user(self.user2)
        
        # No debts initially
        with self.assertRaises(ValueError):
            self.group.settle_debt(self.user1.id, self.user2.id, 10.0)


if __name__ == '__main__':
    unittest.main()
