# Expense Split Tracker

A comprehensive web application for managing shared expenses among groups of users, similar to Splitwise. Built with Python Flask and featuring advanced debt simplification algorithms.

## Problem Statement and Approach

### Problem Statement
When groups of people (friends, family, roommates, or colleagues) share expenses, tracking who owes what to whom becomes complex. Manual calculations are error-prone, and settling debts can require multiple transactions between different people. This application solves these problems by:

1. **Expense Tracking**: Recording shared expenses with different splitting methods
2. **Balance Management**: Automatically calculating who owes money to whom
3. **Debt Simplification**: Minimizing the number of transactions needed to settle all debts
4. **Multi-Currency Support**: Handling expenses in different currencies per group

### Technical Approach
This application uses a **service-oriented architecture** with clear separation of concerns:

- **Models Layer**: Core business entities (User, Group, Expense)
- **Services Layer**: Business logic (ExpenseTracker, DebtSimplifier)
- **Web Layer**: Flask routes and templates with Bootstrap UI
- **Validation Layer**: Input validation and data integrity checks

## Features

### Core Functionality
- ✅ **Group Management**: Create and manage expense-sharing groups
- ✅ **User Management**: Add members to groups with email tracking
- ✅ **Multiple Split Types**:
  - **Equal Split**: Divide expenses equally among participants
  - **Exact Amount Split**: Specify custom amounts for each person
  - **Percentage Split**: Allocate expenses by percentage
- ✅ **Real-time Balance Tracking**: Automatic calculation of who owes what
- ✅ **Debt Simplification**: Minimize transactions using advanced algorithms
- ✅ **Debt Settlement**: Record payments between group members
- ✅ **Multi-Currency Support**: Per-group currency settings

### User Interface
- 🎨 **Dark Theme**: Modern Bootstrap-based dark theme interface
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile devices
- 🔄 **Real-time Updates**: Live preview of split calculations
- 📊 **Visual Analytics**: Group summaries and balance overviews
- ⚡ **Interactive Forms**: Dynamic form validation and feedback

## Setup Instructions

### Prerequisites

- **Python 3.11+**: The application requires Python 3.11 or higher
- **pip**: Python package installer (usually included with Python)
- **Web Browser**: Modern web browser (Chrome, Firefox, Safari, Edge)

### How to Run the Project

#### Option 1: Run on Replit (Recommended)
1. This project is pre-configured for Replit
2. Click the "Run" button in the Replit interface
3. The application will start automatically on port 5000
4. Access the application through the web preview panel

#### Option 2: Local Installation
1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd expense-split-tracker
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   
   Required packages:
   - `flask`: Web framework
   - `gunicorn`: WSGI server for production

3. **Set environment variables** (optional):
   ```bash
   export SESSION_SECRET="your-secret-key-here"
   ```

4. **Run the application**:
   ```bash
   # Development mode
   python app.py
   
   # Production mode with gunicorn
   gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
   ```

5. **Access the application**:
   Open your browser and navigate to `http://localhost:5000`

### Project Structure
```
expense-split-tracker/
├── models/                 # Data models
│   ├── user.py            # User entity
│   ├── group.py           # Group entity
│   └── expense.py         # Expense entity with split types
├── services/              # Business logic services
│   ├── expense_tracker.py # Main expense tracking service
│   └── debt_simplifier.py # Debt simplification algorithms
├── templates/             # HTML templates
│   ├── base.html          # Base template with navigation
│   ├── index.html         # Homepage with group overview
│   ├── group_detail.html  # Group management page
│   ├── add_expense.html   # Expense addition form
│   └── settle_debt.html   # Debt settlement form
├── tests/                 # Test suite
│   └── test_complete_functionality.py
├── utils/                 # Utility modules
│   └── validators.py      # Input validation functions
├── app.py                 # Flask application and routes
├── main.py                # Application entry point
└── README.md              # This documentation
```

## Explanations of Complex Logic and Algorithms

### 1. Debt Simplification Algorithm

The debt simplification is the most complex part of the application. It solves the problem of minimizing transactions needed to settle all debts in a group.

#### Problem Example
Without simplification:
- Alice owes Bob $50
- Bob owes Carol $30  
- Carol owes Alice $20

This requires 3 transactions. With simplification:
- Alice pays Carol $30
- Bob pays Carol $20

Only 2 transactions needed!

#### Algorithm Implementation
Located in `services/debt_simplifier.py`, the algorithm uses a **min-heap/max-heap approach**:

```python
def simplify_debts(balances: Dict[str, float]) -> List[Tuple[str, str, float]]:
    """
    Uses two heaps to match largest debtor with largest creditor.
    Time Complexity: O(n log n) where n is number of users
    Space Complexity: O(n)
    """
    debtors = []    # Max heap for people who owe money (positive balance)
    creditors = []  # Min heap for people owed money (negative balance)
    
    # Separate users into debtors and creditors
    for user_id, balance in balances.items():
        if balance > 0.01:  # Owes money
            heapq.heappush(debtors, (-balance, user_id))
        elif balance < -0.01:  # Owed money  
            heapq.heappush(creditors, (balance, user_id))
    
    transactions = []
    
    # Match largest debtor with largest creditor iteratively
    while debtors and creditors:
        debt_amount, debtor_id = heapq.heappop(debtors)
        credit_amount, creditor_id = heapq.heappop(creditors)
        
        # Calculate settlement amount
        settlement_amount = min(-debt_amount, -credit_amount)
        transactions.append((debtor_id, creditor_id, settlement_amount))
        
        # Handle remaining balances
        remaining_debt = -debt_amount - settlement_amount
        remaining_credit = -credit_amount - settlement_amount
        
        if remaining_debt > 0.01:
            heapq.heappush(debtors, (-remaining_debt, debtor_id))
        if remaining_credit > 0.01:
            heapq.heappush(creditors, (-remaining_credit, creditor_id))
    
    return transactions
```

#### Why This Algorithm Works
1. **Greedy Approach**: Always match the largest debtor with largest creditor
2. **Optimal for Tree-like Debt Graphs**: Guarantees minimum transactions for most practical scenarios
3. **Floating Point Safe**: Uses 0.01 threshold to handle floating-point precision issues

### 2. Balance Calculation System

The balance system tracks who owes money using a simple but effective approach:

#### Balance Rules
- **Positive Balance**: User owes money to the group
- **Negative Balance**: User is owed money by the group  
- **Zero Balance**: User is settled up

#### Expense Processing
When an expense is added:
```python
def _update_balances_for_expense(self, expense: Expense):
    # Person who paid gets credited (negative balance)
    self.balances[expense.paid_by_user_id] -= expense.amount
    
    # Each person in the split gets debited (positive balance)
    for user_id, amount in expense.user_shares.items():
        self.balances[user_id] += amount
```

#### Example Calculation
Expense: Alice pays $300 hotel bill, split equally among Alice, Bob, and Carol ($100 each)

**Before**: All balances are $0
**After**:
- Alice: -$300 + $100 = -$200 (owed $200)
- Bob: +$100 = $100 (owes $100)  
- Carol: +$100 = $100 (owes $100)

### 3. Split Type Implementations

#### Equal Split
```python
split_amount = total_amount / len(participants)
for user_id in participants:
    expense.add_user_share(user_id, split_amount)
```

#### Exact Amount Split
```python
# Validation: amounts must sum to total
if abs(sum(user_amounts.values()) - total_amount) > 0.01:
    raise ValueError("Split amounts don't match total")

for user_id, amount in user_amounts.items():
    expense.add_user_share(user_id, amount)
```

#### Percentage Split
```python
# Validation: percentages must sum to 100%
if abs(sum(user_percentages.values()) - 100.0) > 0.1:
    raise ValueError("Percentages don't sum to 100%")

for user_id, percentage in user_percentages.items():
    amount = total_amount * (percentage / 100)
    expense.add_user_share(user_id, amount)
```

### 4. Data Integrity and Validation

The application includes comprehensive validation to ensure data integrity:

#### Expense Validation
- Amount must be positive
- All users in split must exist in group
- Split amounts must equal total expense amount
- Currency must match group currency

#### User Validation  
- Email format validation (when provided)
- Unique user names within groups
- Users cannot be removed with outstanding balances

#### Financial Validation
- Floating-point precision handling (0.01 thresholds)
- Currency consistency checking
- Settlement amount validation

## Special Considerations

### 1. Floating-Point Precision
Financial calculations require careful handling of floating-point arithmetic:
- Uses 0.01 thresholds for balance comparisons
- Rounds currency amounts to 2 decimal places
- Validates split calculations to prevent accumulation errors

### 2. In-Memory Storage
Current implementation uses in-memory storage for simplicity:
- **Advantages**: Fast, no database setup required
- **Limitations**: Data is lost on restart, not suitable for production
- **Future Enhancement**: Could be extended with PostgreSQL or SQLite

### 3. Scalability Considerations
- Debt simplification algorithm is O(n log n) - efficient for groups up to thousands of users
- Memory usage grows linearly with users and expenses
- Web interface remains responsive with hundreds of expenses per group

### 4. Security Considerations
- No authentication system (demo/development focused)
- Session secrets should be set in production
- Input validation prevents common injection attacks
- No sensitive data storage (passwords, payment info)

## Testing

The application includes comprehensive test coverage:

```bash
# Run all tests
cd tests && python test_complete_functionality.py -v

# Tests cover:
# ✅ Group creation and management
# ✅ User management
# ✅ All three split types (equal, exact, percentage)
# ✅ Balance calculations
# ✅ Debt simplification
# ✅ Debt settlement
# ✅ Error handling and validation
# ✅ Complex multi-expense scenarios
```

### Test Results
All 8 test cases pass, covering:
- Basic CRUD operations
- Complex financial calculations  
- Edge cases and error conditions
- End-to-end functionality

## Technology Stack

### Backend
- **Python 3.11+**: Core language
- **Flask**: Web framework for routing and templating
- **Jinja2**: Template engine (included with Flask)
- **Gunicorn**: WSGI server for production deployment

### Frontend
- **Bootstrap 5**: CSS framework with dark theme
- **Font Awesome**: Icon library
- **Vanilla JavaScript**: Interactive form behavior
- **Responsive Design**: Mobile-first approach

### Development Tools
- **unittest**: Python's built-in testing framework
- **LSP**: Language server for code analysis
- **Git**: Version control

## Sample Data

The application initializes with sample data for demonstration:

### Sample Groups
1. **"Family Trip"** - Summer vacation expenses (USD)
   - Members: Alice Johnson, Bob Smith, Carol Davis
   - Expenses: Hotel ($300), Gas ($150), Restaurant ($240)

2. **"Office Lunch"** - Weekly team lunch expenses (USD)  
   - Members: David Wilson, Eva Brown
   - Expenses: Pizza lunch ($85)

This sample data demonstrates all features and provides realistic scenarios for testing.

## Contributing

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is open source and available under the MIT License.

---

## Loom Video Link

[Demo Video: Expense Split Tracker Walkthrough](https://www.loom.com/share/your-video-id-here)

*Note: Video demonstrates group creation, expense addition with all split types, balance tracking, and debt simplification in action.*

---

**Built with ❤️ using Python Flask and Bootstrap**

*Split expenses, settle debts, simplify life.*