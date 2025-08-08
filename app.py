"""Flask web application for Expense Split Tracker."""

import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, session
from services.expense_tracker import ExpenseTracker
from models.expense import SplitType
from utils.validators import ExpenseValidator, CurrencyValidator

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Initialize expense tracker (in-memory for this implementation)
expense_tracker = ExpenseTracker()

# Add sample data for testing and demonstration
def initialize_sample_data():
    """Initialize sample data for testing and demonstration."""
    try:
        # Create sample groups
        group1 = expense_tracker.create_group("Family Trip", "Summer vacation expenses", "USD")
        group2 = expense_tracker.create_group("Office Lunch", "Weekly team lunch expenses", "USD")
        
        # Add users to Family Trip
        user1 = expense_tracker.add_user_to_group(group1.id, "Alice Johnson", "alice@example.com")
        user2 = expense_tracker.add_user_to_group(group1.id, "Bob Smith", "bob@example.com")
        user3 = expense_tracker.add_user_to_group(group1.id, "Carol Davis", "carol@example.com")
        
        # Add users to Office Lunch
        user4 = expense_tracker.add_user_to_group(group2.id, "David Wilson", "david@example.com")
        user5 = expense_tracker.add_user_to_group(group2.id, "Eva Brown", "eva@example.com")
        
        # Add some expenses to Family Trip
        expense_tracker.add_expense_equal_split(
            group1.id, 300.00, "Hotel Booking", 
            user1.id, [user1.id, user2.id, user3.id]
        )
        
        expense_tracker.add_expense_exact_split(
            group1.id, 150.00, "Gas and Tolls",
            user2.id, {user1.id: 50.00, user2.id: 60.00, user3.id: 40.00}
        )
        
        expense_tracker.add_expense_percentage_split(
            group1.id, 240.00, "Restaurant Dinner",
            user3.id, {user1.id: 40.0, user2.id: 35.0, user3.id: 25.0}
        )
        
        # Add expenses to Office Lunch
        expense_tracker.add_expense_equal_split(
            group2.id, 85.00, "Pizza Lunch",
            user4.id, [user4.id, user5.id]
        )
        
        logging.info("Sample data initialized successfully")
    except Exception as e:
        logging.error(f"Error initializing sample data: {e}")

# Initialize sample data
initialize_sample_data()


@app.route('/')
def index():
    """Homepage showing all groups."""
    groups = expense_tracker.get_all_groups()
    return render_template('index.html', groups=groups)


@app.route('/create_group', methods=['GET', 'POST'])
def create_group():
    """Create a new expense group."""
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            currency = request.form.get('currency', 'USD').strip().upper()
            
            if not name:
                flash('Group name is required', 'error')
                return render_template('create_group.html')
            
            # Validate currency
            try:
                CurrencyValidator.validate_currency(currency)
            except ValueError as e:
                flash(f'Invalid currency: {e}', 'error')
                return render_template('create_group.html')
            
            group = expense_tracker.create_group(name, description, currency)
            flash(f'Group "{name}" created successfully!', 'success')
            return redirect(url_for('group_detail', group_id=group.id))
            
        except Exception as e:
            logging.error(f"Error creating group: {e}")
            flash(f'Error creating group: {str(e)}', 'error')
    
    return render_template('create_group.html')


@app.route('/group/<group_id>')
def group_detail(group_id):
    """Show group details, members, expenses, and balances."""
    try:
        group = expense_tracker.get_group(group_id)
        if not group:
            flash('Group not found', 'error')
            return redirect(url_for('index'))
        
        # Get simplified debts for the group
        simplified_debts = expense_tracker.get_simplified_debts(group_id)
        
        return render_template('group_detail.html', 
                             group=group, 
                             simplified_debts=simplified_debts)
    
    except Exception as e:
        logging.error(f"Error loading group {group_id}: {e}")
        flash(f'Error loading group: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/group/<group_id>/add_user', methods=['POST'])
def add_user_to_group(group_id):
    """Add a new user to a group."""
    try:
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip() or None
        
        if not name:
            flash('User name is required', 'error')
            return redirect(url_for('group_detail', group_id=group_id))
        
        user = expense_tracker.add_user_to_group(group_id, name, email)
        flash(f'User "{name}" added to group successfully!', 'success')
        
    except ValueError as e:
        flash(f'Error adding user: {str(e)}', 'error')
    except Exception as e:
        logging.error(f"Error adding user to group {group_id}: {e}")
        flash(f'Error adding user: {str(e)}', 'error')
    
    return redirect(url_for('group_detail', group_id=group_id))


@app.route('/group/<group_id>/add_expense', methods=['GET', 'POST'])
def add_expense(group_id):
    """Add a new expense to a group."""
    try:
        group = expense_tracker.get_group(group_id)
        if not group:
            flash('Group not found', 'error')
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            # Get basic expense info
            description = request.form.get('description', '').strip()
            amount = float(request.form.get('amount', 0))
            paid_by = request.form.get('paid_by', '').strip()
            split_type = request.form.get('split_type', 'equal')
            
            if not description:
                flash('Expense description is required', 'error')
                return render_template('add_expense.html', group=group)
            
            if not paid_by:
                flash('Please select who paid for the expense', 'error')
                return render_template('add_expense.html', group=group)
            
            # Validate amount
            try:
                ExpenseValidator.validate_amount(amount)
            except ValueError as e:
                flash(f'Invalid amount: {str(e)}', 'error')
                return render_template('add_expense.html', group=group)
            
            # Handle different split types
            try:
                if split_type == 'equal':
                    # Get selected users for equal split
                    equal_users = request.form.getlist('equal_users')
                    if not equal_users:
                        flash('Please select at least one user for equal split', 'error')
                        return render_template('add_expense.html', group=group)
                    
                    expense = expense_tracker.add_expense_equal_split(
                        group_id, amount, description, paid_by, equal_users
                    )
                
                elif split_type == 'exact':
                    # Get exact amounts for each user
                    user_amounts = {}
                    for user_id in group.users.keys():
                        exact_amount = request.form.get(f'exact_{user_id}', 0)
                        if exact_amount:
                            user_amounts[user_id] = float(exact_amount)
                    
                    if not user_amounts:
                        flash('Please specify at least one exact amount', 'error')
                        return render_template('add_expense.html', group=group)
                    
                    expense = expense_tracker.add_expense_exact_split(
                        group_id, amount, description, paid_by, user_amounts
                    )
                
                elif split_type == 'percentage':
                    # Get percentages for each user
                    user_percentages = {}
                    for user_id in group.users.keys():
                        percentage = request.form.get(f'percentage_{user_id}', 0)
                        if percentage:
                            user_percentages[user_id] = float(percentage)
                    
                    if not user_percentages:
                        flash('Please specify at least one percentage', 'error')
                        return render_template('add_expense.html', group=group)
                    
                    expense = expense_tracker.add_expense_percentage_split(
                        group_id, amount, description, paid_by, user_percentages
                    )
                
                else:
                    flash('Invalid split type', 'error')
                    return render_template('add_expense.html', group=group)
                
                flash(f'Expense "{description}" added successfully!', 'success')
                return redirect(url_for('group_detail', group_id=group_id))
            
            except ValueError as e:
                flash(f'Error adding expense: {str(e)}', 'error')
                return render_template('add_expense.html', group=group)
        
        return render_template('add_expense.html', group=group)
    
    except Exception as e:
        logging.error(f"Error in add_expense for group {group_id}: {e}")
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('group_detail', group_id=group_id))


@app.route('/group/<group_id>/settle_debt', methods=['GET', 'POST'])
def settle_debt(group_id):
    """Settle debt between users in a group."""
    try:
        group = expense_tracker.get_group(group_id)
        if not group:
            flash('Group not found', 'error')
            return redirect(url_for('index'))
        
        # Get simplified debts for suggestions
        simplified_debts = expense_tracker.get_simplified_debts(group_id)
        
        if request.method == 'POST':
            payer_id = request.form.get('payer', '').strip()
            payee_id = request.form.get('payee', '').strip()
            amount = float(request.form.get('amount', 0))
            
            if not payer_id or not payee_id:
                flash('Please select both payer and recipient', 'error')
                return render_template('settle_debt.html', group=group, simplified_debts=simplified_debts)
            
            if payer_id == payee_id:
                flash('Payer and recipient cannot be the same person', 'error')
                return render_template('settle_debt.html', group=group, simplified_debts=simplified_debts)
            
            if amount <= 0:
                flash('Settlement amount must be positive', 'error')
                return render_template('settle_debt.html', group=group, simplified_debts=simplified_debts)
            
            try:
                success = expense_tracker.settle_debt(group_id, payer_id, payee_id, amount)
                if success:
                    payer_name = group.users[payer_id].name
                    payee_name = group.users[payee_id].name
                    flash(f'{payer_name} paid {payee_name} {group.currency}{amount:.2f} - debt settled!', 'success')
                    return redirect(url_for('group_detail', group_id=group_id))
            
            except ValueError as e:
                flash(f'Settlement error: {str(e)}', 'error')
                return render_template('settle_debt.html', group=group, simplified_debts=simplified_debts)
        
        return render_template('settle_debt.html', group=group, simplified_debts=simplified_debts)
    
    except Exception as e:
        logging.error(f"Error in settle_debt for group {group_id}: {e}")
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('group_detail', group_id=group_id))


@app.route('/group/<group_id>/summary')
def group_summary(group_id):
    """Get comprehensive group summary (API endpoint)."""
    try:
        summary = expense_tracker.get_group_summary(group_id)
        return summary
    except ValueError as e:
        return {'error': str(e)}, 404
    except Exception as e:
        logging.error(f"Error getting group summary {group_id}: {e}")
        return {'error': 'Internal server error'}, 500


# Template for create_group that's missing
@app.route('/create_group_form')
def create_group_form():
    """Render create group form."""
    return render_template('create_group.html')


# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    return render_template('error.html', 
                         error_code=404,
                         error_message="Page not found"), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logging.error(f"Internal server error: {error}")
    return render_template('error.html',
                         error_code=500, 
                         error_message="Internal server error"), 500


# Template context processors
@app.context_processor
def utility_processor():
    """Add utility functions to template context."""
    def format_currency(amount, currency='USD'):
        """Format currency for display."""
        return f"{currency}{amount:.2f}"
    
    def get_balance_class(balance):
        """Get CSS class for balance display."""
        if balance > 0.01:
            return 'text-danger'  # Owes money
        elif balance < -0.01:
            return 'text-success'  # Owed money
        else:
            return 'text-secondary'  # Settled
    
    def get_balance_text(balance):
        """Get display text for balance."""
        if balance > 0.01:
            return f'owes {abs(balance):.2f}'
        elif balance < -0.01:
            return f'owed {abs(balance):.2f}'
        else:
            return 'settled'
    
    return dict(format_currency=format_currency,
                get_balance_class=get_balance_class,
                get_balance_text=get_balance_text)


# Development seed data (optional, for testing)
def create_sample_data():
    """Create sample data for development/testing."""
    if app.debug and len(expense_tracker.get_all_groups()) == 0:
        # Create a sample group
        group = expense_tracker.create_group(
            "Trip to Paris", 
            "Vacation expenses with friends", 
            "USD"
        )
        
        # Add sample users
        user1 = expense_tracker.add_user_to_group(group.id, "Alice", "alice@example.com")
        user2 = expense_tracker.add_user_to_group(group.id, "Bob", "bob@example.com")
        user3 = expense_tracker.add_user_to_group(group.id, "Charlie", "charlie@example.com")
        
        # Add sample expenses
        expense_tracker.add_expense_equal_split(
            group.id, 120.0, "Dinner at restaurant", user1.id, 
            [user1.id, user2.id, user3.id]
        )
        
        expense_tracker.add_expense_exact_split(
            group.id, 80.0, "Taxi to airport", user2.id,
            {user1.id: 30.0, user2.id: 25.0, user3.id: 25.0}
        )
        
        logging.info("Sample data created for development")


if __name__ == '__main__':
    # Create sample data in debug mode
    create_sample_data()
    
    # Run the Flask application
    app.run(host='0.0.0.0', port=5000, debug=True)
