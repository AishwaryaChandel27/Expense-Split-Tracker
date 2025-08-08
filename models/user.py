"""User model for expense tracking."""

from typing import Dict, Any, Optional
import uuid


class User:
    """Represents a user in the expense tracking system."""
    
    def __init__(self, name: str, email: Optional[str] = None):
        """Initialize a new user.
        
        Args:
            name: The user's display name
            email: Optional email address
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.email = email
        self.created_at = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'created_at': self.created_at
        }
    
    def __str__(self) -> str:
        return f"User({self.name})"
    
    def __repr__(self) -> str:
        return f"User(id={self.id}, name={self.name})"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, User):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
