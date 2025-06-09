# -*- coding: utf-8 -*-
"""
Result Formatters
Utilities for formatting and displaying analysis results
"""

import logging
from typing import List, Dict, Any, Optional
from tabulate import tabulate

from config.settings import (
    TABLE_FORMAT, 
    MAX_PERMLINK_LENGTH, 
    MESSAGES
)

logger = logging.getLogger(__name__)


class ResultFormatter:
    """Formats analysis results for display"""
    
    def __init__(self, language: str = 'it'):
        self.language = language
        self.messages = MESSAGES.get(language, MESSAGES['it'])
    
    def format_results(self, results: List[Dict[str, Any]], username: Optional[str] = None) -> None:
        """Format and display results in a table"""
        if not results:
            print(self.messages['no_results'])
            return
        
        # Prepare table data
        table_data = []
        for op in results:
            row = self._format_operation_row(op, username)
            table_data.append(row)
        
        # Display table
        headers = [
            'Timestamp', 'Author', 'Permlink', 'Reward', 
            'Vote Weight', 'Days to Reward', 'Est. Value'
        ]
        print(tabulate(table_data, headers=headers, tablefmt=TABLE_FORMAT))
        
        # Display statistics
        self._display_statistics(results)
    
    def _format_operation_row(self, op: Dict[str, Any], username: Optional[str] = None) -> List[str]:
        """Format a single operation row for the table"""
        reward_amount = op.get('reward', 'N/A')
        comment_author = op.get('comment_author', 'N/A')
        comment_permlink = op.get('comment_permlink', 'N/A')
        timestamp = op.get('timestamp', 'N/A')
        
        # Vote information
        vote_info = op.get('vote_info', {})
        vote_weight = vote_info.get('weight', 'N/A') if vote_info else 'N/A'
        days_to_reward = op.get('days_to_reward', 'N/A')
        
        # Calculate estimated vote value
        estimated_value = 'N/A'
        if vote_info and username and isinstance(vote_weight, (int, float)):
            try:
                # Use pre-calculated value if available
                vote_value_steem = op.get('vote_value_steem')
                if vote_value_steem is not None:
                    estimated_value = f"${vote_value_steem:.4f}"
            except Exception as e:
                logger.debug(f"Error formatting vote value: {e}")
        
        # Format permlink
        if len(comment_permlink) > MAX_PERMLINK_LENGTH:
            comment_permlink = comment_permlink[:MAX_PERMLINK_LENGTH] + '...'
        
        # Format days to reward
        days_str = (
            f"{days_to_reward:.1f}" 
            if isinstance(days_to_reward, (int, float)) 
            else str(days_to_reward)
        )
        
        return [
            str(timestamp),
            str(comment_author),
            str(comment_permlink),
            str(reward_amount),
            str(vote_weight),
            days_str,
            str(estimated_value)
        ]
    
    def _display_statistics(self, results: List[Dict[str, Any]]) -> None:
        """Display summary statistics"""
        total_rewards = len(results)
        rewards_with_votes = len([op for op in results if 'vote_info' in op])
        
        print(f"\n{self.messages['statistics']}")
        print(self.messages['total_rewards'].format(count=total_rewards))
        print(self.messages['matched_rewards'].format(count=rewards_with_votes))
        
        if total_rewards > 0:
            percentage = (rewards_with_votes / total_rewards) * 100
            print(self.messages['match_percentage'].format(percentage=percentage))
        else:
            print(self.messages['match_percentage'].format(percentage="N/A"))
    
    def display_analysis_header(self, username: str, days_back: int, node_urls: List[str]) -> None:
        """Display analysis header information"""
        print("=== ANALIZZATORE CURATOR STEEM ===")
        print(f"Curator: {username}")
        print("Nodi utilizzati:")
        for node in node_urls:
            print(f"  - {node}")
        print()
        
        print(self.messages['analyzing'].format(username=username, days=days_back))
        print(self.messages['connecting'])
