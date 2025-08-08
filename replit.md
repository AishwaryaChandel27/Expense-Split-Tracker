# Expense Split Tracker

## Overview

The Expense Split Tracker is a Flask-based web application that helps users manage shared expenses among groups. The system allows users to create groups (e.g., for trips or events), add expenses with various splitting methods, track balances between members, and settle debts. The application supports three splitting methods: equal splits, exact amount splits, and percentage-based splits, with built-in debt simplification to minimize the number of transactions needed for settlement.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask web application with a service-oriented architecture
- **Data Models**: In-memory data storage using Python classes (User, Group, Expense)
- **Services Layer**: Modular services for expense tracking and debt simplification
- **Validation Layer**: Input validation utilities for expenses and currency handling

### Core Components

**Models Layer**:
- `User`: Represents individual users with unique IDs and basic profile information
- `Group`: Manages collections of users sharing expenses with currency tracking
- `Expense`: Handles expense records with multiple split types (equal, exact, percentage)

**Services Layer**:
- `ExpenseTracker`: Main orchestrator for group and expense management operations
- `DebtSimplifier`: Implements algorithms to minimize transactions for debt settlement

**Web Layer**:
- Flask routes handling group creation, expense addition, and debt settlement
- Template-based UI using Bootstrap for responsive design
- Form handling with server-side validation and flash messaging

### Data Flow Architecture
The system follows a request-response pattern where:
1. User actions trigger Flask route handlers
2. Route handlers validate input and delegate to service layer
3. Services manipulate model objects and update in-memory state
4. Results are rendered through Jinja2 templates with Bootstrap styling

### Split Logic Implementation
- **Equal Split**: Divides total amount equally among specified participants
- **Exact Split**: Allows custom amounts per user with validation for total sum
- **Percentage Split**: Distributes based on percentage allocation with sum validation

### Balance Tracking System
- Maintains per-user balances within each group (positive = owes money, negative = owed money)
- Updates balances automatically when expenses are added or debts are settled
- Provides real-time balance calculations for settlement recommendations

## External Dependencies

### Frontend Dependencies
- **Bootstrap 5**: CSS framework for responsive UI design
- **Font Awesome**: Icon library for enhanced visual elements
- **CDN-delivered assets**: External hosting for CSS and JavaScript libraries

### Python Package Dependencies
- **Flask**: Core web framework for routing and templating
- **Standard Library**: Uses built-in Python modules (uuid, datetime, enum, typing) for core functionality

### Development Dependencies
- **unittest**: Built-in testing framework for unit tests
- **logging**: Standard library logging for debugging and monitoring

### Data Storage
- **In-Memory Storage**: Current implementation uses Python dictionaries and objects
- **No Database**: No external database dependencies in current architecture
- **Session Management**: Flask sessions for user state management

Note: The current architecture uses in-memory storage, making it suitable for development and demonstration purposes. For production deployment, integration with a persistent database system would be recommended.