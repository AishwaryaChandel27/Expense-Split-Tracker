"""Tests for DebtSimplifier service."""

import unittest
from services.debt_simplifier import DebtSimplifier


class TestDebtSimplifier(unittest.TestCase):
    """Test cases for DebtSimplifier service."""
    
    def test_simple_debt_simplification(self):
        """Test basic debt simplification."""
        balances = {
            'user1': -30.0,  # Owed $30
            'user2': 20.0,   # Owes $20
            'user3': 10.0    # Owes $10
        }
        
        transactions = DebtSimplifier.simplify_debts(balances)
        
        # Should have 2 transactions
        self.assertEqual(len(transactions), 2)
        
        # Verify total amount
        total_amount = sum(amount for _, _, amount in transactions)
        self.assertAlmostEqual(total_amount, 30.0, places=2)
        
        # Verify all transactions involve user1 as payee (since they're owed money)
        for payer, payee, amount in transactions:
            self.assertEqual(payee, 'user1')
            self.assertIn(payer, ['user2', 'user3'])
    
    def test_complex_debt_simplification(self):
        """Test more complex debt scenario."""
        balances = {
            'user1': -50.0,  # Owed $50
            'user2': 30.0,   # Owes $30
            'user3': 20.0,   # Owes $20
            'user4': 0.0,    # Even
            'user5': -10.0,  # Owed $10
            'user6': 10.0    # Owes $10
        }
        
        transactions = DebtSimplifier.simplify_debts(balances)
        
        # Should minimize number of transactions
        self.assertLessEqual(len(transactions), 4)
        
        # Verify conservation of money
        total_debt = sum(max(0, balance) for balance in balances.values())
        total_credit = sum(max(0, -balance) for balance in balances.values())
        total_transactions = sum(amount for _, _, amount in transactions)
        
        self.assertAlmostEqual(total_debt, total_credit, places=2)
        self.assertAlmostEqual(total_transactions, total_debt, places=2)
    
    def test_no_debts(self):
        """Test case with no debts."""
        balances = {
            'user1': 0.0,
            'user2': 0.0,
            'user3': 0.0
        }
        
        transactions = DebtSimplifier.simplify_debts(balances)
        self.assertEqual(len(transactions), 0)
    
    def test_single_debt(self):
        """Test case with single debt."""
        balances = {
            'user1': -50.0,  # Owed $50
            'user2': 50.0    # Owes $50
        }
        
        transactions = DebtSimplifier.simplify_debts(balances)
        
        self.assertEqual(len(transactions), 1)
        payer, payee, amount = transactions[0]
        self.assertEqual(payer, 'user2')
        self.assertEqual(payee, 'user1')
        self.assertAlmostEqual(amount, 50.0, places=2)
    
    def test_debt_graph_calculation(self):
        """Test debt graph calculation."""
        balances = {
            'user1': -40.0,  # Owed $40
            'user2': 25.0,   # Owes $25
            'user3': 15.0    # Owes $15
        }
        
        debt_graph = DebtSimplifier.calculate_debt_graph(balances)
        
        # Check structure
        self.assertIn('user2', debt_graph)
        self.assertIn('user3', debt_graph)
        self.assertIn('user1', debt_graph['user2'])
        self.assertIn('user1', debt_graph['user3'])
        
        # Check amounts
        self.assertAlmostEqual(debt_graph['user2']['user1'], 25.0, places=2)
        self.assertAlmostEqual(debt_graph['user3']['user1'], 15.0, places=2)
    
    def test_user_debt_summary(self):
        """Test user debt summary generation."""
        balances = {
            'user1': -30.0,  # Owed $30
            'user2': 20.0,   # Owes $20
            'user3': 10.0    # Owes $10
        }
        
        # Summary for user1 (owed money)
        summary1 = DebtSimplifier.get_user_debt_summary('user1', balances)
        self.assertEqual(summary1['total_owes'], 0.0)
        self.assertEqual(summary1['total_owed'], 30.0)
        self.assertEqual(summary1['net_balance'], -30.0)
        
        # Summary for user2 (owes money)
        summary2 = DebtSimplifier.get_user_debt_summary('user2', balances)
        self.assertEqual(summary2['total_owes'], 20.0)
        self.assertEqual(summary2['total_owed'], 0.0)
        self.assertEqual(summary2['net_balance'], 20.0)
    
    def test_simplification_validation(self):
        """Test validation of simplification results."""
        balances = {
            'user1': -50.0,
            'user2': 30.0,
            'user3': 20.0
        }
        
        transactions = DebtSimplifier.simplify_debts(balances)
        is_valid = DebtSimplifier.validate_simplification(balances, transactions)
        
        self.assertTrue(is_valid)
    
    def test_edge_case_small_amounts(self):
        """Test handling of very small amounts."""
        balances = {
            'user1': -0.005,  # Very small amount owed
            'user2': 0.005    # Very small amount owes
        }
        
        transactions = DebtSimplifier.simplify_debts(balances)
        
        # Should not create transactions for amounts smaller than threshold
        self.assertEqual(len(transactions), 0)


if __name__ == '__main__':
    unittest.main()
