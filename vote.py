from beem import Steem
from beem.account import Account

import logging
from datetime import datetime, timezone, timedelta
from beem.comment import Comment
from tabulate import tabulate
import requests
from beem.utils import formatTimeString

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_vote_value(self, curator, vote_percent, effective_vests=None, voting_power=9200):
        """Calculate vote value based on blockchain parameters, similar to the JS implementation."""
        try:
            # Step 1: Get dynamic global properties
            steem = Steem(node=self.node_urls['steem'])
            props = steem.get_dynamic_global_properties()
            
            # Step 2: Calculate SP/VESTS ratio
            total_vesting_fund_steem = float(props['total_vesting_fund_steem'].split(' ')[0])
            total_vesting_shares = float(props['total_vesting_shares'].split(' ')[0])
            steem_per_vests = total_vesting_fund_steem / total_vesting_shares
            
            # Step 3: If no vesting shares provided, use current user's
            vesting_shares = effective_vests
            if not vesting_shares:
                # Usiamo blockchain_connector invece di blockchain
                account = Account(curator, blockchain_instance=steem)
                if not account:
                    raise Exception('Unable to get account info')
                
                # Ottieni i vesting shares dall'account
                account_vests = float(account['vesting_shares'].amount)
                delegated_out = float(account['delegated_vesting_shares'].amount)
                received_vests = float(account['received_vesting_shares'].amount)
                vesting_shares = account_vests - delegated_out + received_vests
            
            # Step 4: Convert vests to Steem Power
            sp = vesting_shares * steem_per_vests
            
            # Step 5: Calculate 'r' (SP/spv ratio)
            r = sp / steem_per_vests
            
            # Step 6: Calculate 'p' (voting power)
            weight = vote_percent  # Convert percentage to weight (100% = 10000)
            p = (voting_power * weight / 10000 + 49) / 50
            
            # Step 7: Get reward fund con il nuovo metodo - utilizziamo blockchain_connector
            reward_fund = steem.get_reward_fund("post")
            
            # Step 8: Calculate rbPrc
            recent_claims = float(reward_fund['recent_claims'])
            # Controlla il formato e adatta di conseguenza
            if 'reward_balance' in reward_fund:
                if isinstance(reward_fund['reward_balance'], str):
                    reward_balance = float(reward_fund['reward_balance'].split(' ')[0])
                else:
                    reward_balance = float(reward_fund['reward_balance'].amount)
            else:
                raise Exception("Format of reward_fund not recognized")
                
            rb_prc = reward_balance / recent_claims
            
            # Step 9: Get median price con il nuovo metodo - utilizziamo blockchain_connector
            price_info = steem.get_current_median_history_price()
            
            base_amount = float(price_info['base']['amount'])
            quote_amount = float(price_info['quote']['amount'])
            steem_to_sbd_rate = base_amount / quote_amount
            
            # Step 10: Apply the official Steem formula
            steem_value = r * p * 100 * rb_prc
            
            # Convert STEEM to USD/SBD using the median price
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