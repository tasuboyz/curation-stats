# -*- coding: utf-8 -*-
"""
Validators
Input validation utilities
"""

import re
from typing import Optional
from datetime import datetime, timezone


class InputValidator:
    """Validates user inputs and data"""
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """
        Validate Steem username format
        
        Args:
            username: Username to validate
            
        Returns:
            True if valid username format
        """
        if not username or not isinstance(username, str):
            return False
        
        # Steem usernames: 3-16 characters, lowercase letters, numbers, dots, dashes
        pattern = r'^[a-z0-9.-]{3,16}$'
        return bool(re.match(pattern, username.lower()))
    
    @staticmethod
    def validate_days_back(days: int) -> bool:
        """
        Validate days_back parameter
        
        Args:
            days: Number of days to validate
            
        Returns:
            True if valid days range
        """
        return isinstance(days, int) and 1 <= days <= 365
    
    @staticmethod
    def validate_vote_weight(weight: int) -> bool:
        """
        Validate vote weight parameter
        
        Args:
            weight: Vote weight to validate
            
        Returns:
            True if valid vote weight
        """
        return isinstance(weight, int) and -10000 <= weight <= 10000
    
    @staticmethod
    def validate_voting_power(power: int) -> bool:
        """
        Validate voting power parameter
        
        Args:
            power: Voting power to validate
            
        Returns:
            True if valid voting power
        """
        return isinstance(power, int) and 0 <= power <= 10000
    
    @staticmethod
    def sanitize_username(username: str) -> Optional[str]:
        """
        Sanitize and normalize username
        
        Args:
            username: Username to sanitize
            
        Returns:
            Sanitized username or None if invalid
        """
        if not username or not isinstance(username, str):
            return None
        
        # Remove @ symbol if present, convert to lowercase, strip whitespace
        clean_username = username.strip().lower().lstrip('@')
        
        if InputValidator.validate_username(clean_username):
            return clean_username
        
        return None
    
    @staticmethod
    def validate_timestamp(timestamp) -> bool:
        """
        Validate timestamp format
        
        Args:
            timestamp: Timestamp to validate
            
        Returns:
            True if valid timestamp
        """
        if isinstance(timestamp, datetime):
            return True
        
        if isinstance(timestamp, str):
            try:
                datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S')
                return True
            except ValueError:
                try:
                    datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    return True
                except ValueError:
                    return False
        
        return False
