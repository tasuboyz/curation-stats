# -*- coding: utf-8 -*-
"""
Curator Service
Main business logic for analyzing curator activity and curation rewards
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from beem.comment import Comment

from network.steem_connector import SteemConnector
from services.vote_calculator import VoteCalculator
from config.settings import (
    DEFAULT_BATCH_SIZE, 
    VOTE_BUFFER_DAYS,
    MESSAGES
)

logger = logging.getLogger(__name__)


class CuratorService:
    """Service for analyzing curator activity and rewards"""
    
    def __init__(self, connector: SteemConnector):
        self.connector = connector
        self.vote_calculator = VoteCalculator(connector)
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string to datetime object"""
        if not isinstance(timestamp_str, str):
            return timestamp_str
            
        try:
            return datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)
        except ValueError:
            try:
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except Exception:
                return None
    
    def get_user_votes_by_days_back(self, username: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """
        Get curation rewards with corresponding vote information
        
        Args:
            username: Username of the curator
            days_back: Number of days to look back for rewards
            
        Returns:
            List of combined operations with reward and vote data
        """
        account = self.connector.get_account(username)
        if not account:
            logger.error(MESSAGES['it']['all_nodes_failed'])
            return []
        
        steem = self.connector.get_steem_instance()
        if not steem:
            return []
        
        # Calculate date ranges
        reward_cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        vote_cutoff_date = reward_cutoff_date - timedelta(days=VOTE_BUFFER_DAYS)
        
        # Process operations in batches
        virtual_op = account.virtual_op_count()
        batch_size = DEFAULT_BATCH_SIZE
        start_from = virtual_op
        stop = 0
        
        recent_votes = {}
        curation_rewards = []
        still_in_range = True
        
        while still_in_range and start_from > stop:
            batch_stop = max(0, start_from - batch_size)
            operations = list(account.history_reverse(
                start=start_from, 
                stop=batch_stop, 
                use_block_num=False
            ))
            
            # Process batch of operations
            for op in operations:
                op_timestamp = self._parse_timestamp(op.get('timestamp'))
                
                # Stop if we've reached operations older than vote cutoff
                if op_timestamp and op_timestamp < vote_cutoff_date:
                    still_in_range = False
                    break
                
                # Collect vote operations
                if op.get('type') == 'vote' and op.get('voter') == username:
                    vote_key = f"{op.get('author')}/{op.get('permlink')}"
                    recent_votes[vote_key] = op
                
                # Collect curation rewards
                elif (op.get('type') == 'curation_reward' and 
                      op_timestamp and 
                      op_timestamp >= reward_cutoff_date):
                    curation_rewards.append(op)
            
            start_from = batch_stop
        
        # Match rewards with votes and enrich data
        return self._combine_rewards_with_votes(
            curation_rewards, 
            recent_votes, 
            username, 
            steem
        )
    
    def _combine_rewards_with_votes(
        self, 
        rewards: List[Dict[str, Any]], 
        votes: Dict[str, Dict[str, Any]], 
        username: str, 
        steem
    ) -> List[Dict[str, Any]]:
        """Combine curation rewards with corresponding vote information"""
        combined_operations = []
        
        for reward in rewards:
            comment_author = reward.get('comment_author')
            comment_permlink = reward.get('comment_permlink')
            vote_key = f"{comment_author}/{comment_permlink}"
            
            # Create combined operation
            combined_op = reward.copy()
            
            # Add vote information if available
            if vote_key in votes:
                vote_info = votes[vote_key]
                combined_op['vote_info'] = vote_info
                
                try:
                    # Get comment details
                    comment = Comment(
                        f"@{comment_author}/{comment_permlink}", 
                        blockchain_instance=steem
                    )
                    created_post = comment['created']
                    combined_op['active_votes'] = comment['active_votes']
                    
                    # Calculate reward in SP
                    vesting_shares = float(combined_op['reward']['amount']) / (
                        10 ** combined_op['reward']['precision']
                    )
                    combined_op['reward_sp'] = steem.vests_to_sp(vesting_shares)
                    
                    # Calculate vote value
                    vote_value = self.vote_calculator.calculate_vote_value(
                        username, 
                        vote_info['weight']
                    )
                    combined_op['vote_value_steem'] = vote_value['steem_value']
                    
                    # Calculate timing metrics
                    vote_time = self._parse_timestamp(vote_info['timestamp'])
                    if vote_time:
                        combined_op['voted_after_minutes'] = (
                            vote_time - created_post
                        ).total_seconds() / 60
                        
                        reward_time = self._parse_timestamp(reward['timestamp'])
                        if reward_time:
                            combined_op['days_to_reward'] = (
                                reward_time - vote_time
                            ).total_seconds() / 86400
                            
                except (ValueError, TypeError, Exception) as e:
                    logger.debug(f"Error enriching operation data: {e}")
            
            combined_operations.append(combined_op)
        
        return combined_operations
