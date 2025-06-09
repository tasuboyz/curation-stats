# -*- coding: utf-8 -*-
"""
Vote Value Calculator
Handles calculation of vote values based on Steem blockchain parameters
"""

import logging
from typing import Dict, Any, Optional

from ..network.steem_connector import SteemConnector
from ..config.settings import DEFAULT_VOTING_POWER, API_ENDPOINTS

logger = logging.getLogger(__name__)


class VoteCalculator:
    """Calculates vote values using Steem blockchain parameters"""
    
    def __init__(self, connector: SteemConnector):
        self.connector = connector
    
    def get_reward_fund(self, fund_name: str = "post") -> Optional[Dict[str, Any]]:
        """Get reward fund information from blockchain"""
        return self.connector.make_api_call(
            API_ENDPOINTS['reward_fund'], 
            [fund_name]
        )
    
    def get_current_median_history_price(self) -> Optional[Dict[str, Any]]:
        """Get current median price history from blockchain"""
        result = self.connector.make_api_call(API_ENDPOINTS['median_price'])
        
        if result:
            # Parse price data into structured format
            base_parts = result['base'].split(' ')
            quote_parts = result['quote'].split(' ')
            
            return {
                'base': {
                    'amount': float(base_parts[0]),
                    'symbol': base_parts[1]
                },
                'quote': {
                    'amount': float(quote_parts[0]),
                    'symbol': quote_parts[1]
                }
            }
        return None
    
    def calculate_vote_value(
        self, 
        curator: str, 
        vote_percent: int, 
        effective_vests: Optional[float] = None, 
        voting_power: int = DEFAULT_VOTING_POWER
    ) -> Dict[str, Any]:
        """
        Calculate vote value based on blockchain parameters
        
        Args:
            curator: Username of the curator
            vote_percent: Vote weight percentage
            effective_vests: Optional effective vesting shares
            voting_power: Voting power (default 9200)
            
        Returns:
            Dictionary with calculated values and formula components
        """
        try:
            steem = self.connector.get_steem_instance()
            if not steem:
                raise Exception("Unable to connect to Steem")
            
            # Step 1: Get dynamic global properties
            props = steem.get_dynamic_global_properties()
            
            # Step 2: Calculate SP/VESTS ratio
            total_vesting_fund_steem = float(props['total_vesting_fund_steem']['amount'])
            total_vesting_shares = float(props['total_vesting_shares']['amount'])
            steem_per_vests = total_vesting_fund_steem / total_vesting_shares
            
            # Step 3: Get vesting shares
            vesting_shares = effective_vests
            if not vesting_shares:
                account = self.connector.get_account(curator)
                if not account:
                    raise Exception('Unable to get account info')
                
                account_vests = float(account['vesting_shares'].amount)
                delegated_out = float(account['delegated_vesting_shares'].amount)
                received_vests = float(account['received_vesting_shares'].amount)
                vesting_shares = account_vests - delegated_out + received_vests
            
            # Step 4: Convert vests to Steem Power
            sp = vesting_shares * steem_per_vests
            
            # Step 5: Calculate 'r' (SP/spv ratio)
            r = sp / steem_per_vests
            
            # Step 6: Calculate 'p' (voting power)
            weight = vote_percent
            p = (voting_power * weight / 10000 + 49) / 50
            
            # Step 7: Get reward fund
            reward_fund = self.get_reward_fund("post")
            if not reward_fund:
                raise Exception("Unable to get reward fund")
            
            # Step 8: Calculate rbPrc
            recent_claims = float(reward_fund['recent_claims'])
            
            if 'reward_balance' in reward_fund:
                if isinstance(reward_fund['reward_balance'], str):
                    reward_balance = float(reward_fund['reward_balance'].split(' ')[0])
                else:
                    reward_balance = float(reward_fund['reward_balance'].amount)
            else:
                raise Exception("Format of reward_fund not recognized")
                
            rb_prc = reward_balance / recent_claims
            
            # Step 9: Get median price
            price_info = self.get_current_median_history_price()
            if not price_info:
                raise Exception("Unable to get price info")
            
            base_amount = float(price_info['base']['amount'])
            quote_amount = float(price_info['quote']['amount'])
            steem_to_sbd_rate = base_amount / quote_amount
            
            # Step 10: Apply the official Steem formula
            steem_value = r * p * 100 * rb_prc
            usd_value = steem_value * steem_to_sbd_rate
            
            logger.info(f"""Vote Value Calculation:
            - SP: {sp:.3f}
            - Vote Weight: {weight}
            - Voting Power: {voting_power}
            - Price ratio: {steem_to_sbd_rate:.4f}
            - Result: {steem_value:.4f} STEEM (${usd_value:.4f})""")
            
            return {
                "steem_value": float(f"{steem_value:.4f}"),
                "sbd_value": float(f"{usd_value:.4f}"),
                "formula": {
                    "r": r,
                    "p": p,
                    "rb_prc": rb_prc,
                    "median": steem_to_sbd_rate
                }
            }
            
        except Exception as e:
            logger.error(f'Error calculating vote value: {str(e)}')
            return {
                "steem_value": 0,
                "sbd_value": 0,
                "error": str(e)
            }
