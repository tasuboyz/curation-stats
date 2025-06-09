from beem import Steem
from beem.account import Account
from beem.comment import Comment
from datetime import datetime, timezone, timedelta
import logging
import requests
from tabulate import tabulate
from beem.utils import formatTimeString

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CuratorAnalyzer:
    def __init__(self):
        self.node_urls = {
            'steem': [
                "https://api.moecki.online",
                "https://api.steemit.com",
                "https://api.justyy.com"
            ]
        }
    
    def ping_server(self, url):
        """Test if server is reachable"""
        try:
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_user_votes_by_days_back(self, username, days_back=7):
        """
        Returns list of curation rewards with corresponding vote information
        for the past days_back days, properly matching rewards with their votes
        which typically occurred at least 7 days earlier.
        """
        for node_url in self.node_urls.get('steem'):
            if not self.ping_server(node_url):
                logger.error(f"Impossibile raggiungere il server: {node_url}")
                continue
    
            steem = Steem(node=node_url)
            account = Account(username, blockchain_instance=steem)
            
            # Look for rewards in the specified days_back period
            reward_cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
            # Look for votes from a longer period (rewards come ~7 days after votes)
            vote_cutoff_date = reward_cutoff_date - timedelta(days=14)  # Extra buffer to ensure all votes are captured
            
            # Process in batches using virtual operations
            virtual_op = account.virtual_op_count()
            batch_size = 500
            start_from = virtual_op
            stop = 0
            
            recent_votes = {}
            curation_rewards = []
            still_in_range = True
            
            while still_in_range and start_from > stop:
                batch_stop = max(0, start_from - batch_size)
                operations = list(account.history_reverse(start=start_from, stop=batch_stop, use_block_num=False))
                
                # Process this batch of operations
                for op in operations:
                    # Parse and validate timestamp
                    op_timestamp = op.get('timestamp')
                    if isinstance(op_timestamp, str):
                        try:
                            op_timestamp = datetime.strptime(op_timestamp, '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)
                        except ValueError:
                            try:
                                op_timestamp = datetime.fromisoformat(op_timestamp.replace('Z', '+00:00'))
                            except Exception:
                                op_timestamp = None
                    
                    # If we've reached operations older than our vote cutoff, we can stop
                    if op_timestamp and op_timestamp < vote_cutoff_date:
                        still_in_range = False
                        break
                        
                    # Collect vote operations (up to the extended cutoff date)
                    if op.get('type') == 'vote' and op.get('voter') == username:
                        vote_key = f"{op.get('author')}/{op.get('permlink')}"
                        recent_votes[vote_key] = op
                    
                    # Collect curation rewards (only up to the specified days_back)
                    elif op.get('type') == 'curation_reward' and op_timestamp and op_timestamp >= reward_cutoff_date:
                        curation_rewards.append(op)
                
                # Move to the next batch
                start_from = batch_stop
            
            # Match curation rewards with votes
            combined_operations = []
            for reward in curation_rewards:
                comment_author = reward.get('comment_author')
                comment_permlink = reward.get('comment_permlink')
                vote_key = f"{comment_author}/{comment_permlink}"
                comment = Comment(f"@{comment_author}/{comment_permlink}", blockchain_instance=steem)
                created_post = comment['created']
                # Create combined operation
                combined_op = reward.copy()
                
                # Try to add vote info if available
                if vote_key in recent_votes:
                    vote_info = recent_votes[vote_key]
                    combined_op['vote_info'] = vote_info
                    
                    # Calculate time between vote and reward
                    if 'timestamp' in vote_info and isinstance(vote_info['timestamp'], str):
                        try:
                            combined_op['active_votes'] = comment['active_votes']
                            vesting_shares = float(combined_op['reward']['amount']) / (10 ** combined_op['reward']['precision'])
                            vote_value = self.calculate_vote_value(
                                username, 
                                vote_info['weight'], 
                            )
                            combined_op['vote_value_steem'] = vote_value['steem_value']
                            combined_op['reward_sp'] = steem.vests_to_sp(vesting_shares)
                            vote_time = datetime.strptime(vote_info['timestamp'], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)
                            combined_op['voted_after_minutes'] = (vote_time - created_post).total_seconds() / 60
                            reward_time = datetime.strptime(reward['timestamp'], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc) if isinstance(reward['timestamp'], str) else reward['timestamp']
                            combined_op['days_to_reward'] = (reward_time - vote_time).total_seconds() / 86400  # Convert to days
                        except (ValueError, TypeError):
                            pass
                
                combined_operations.append(combined_op)
            
            return combined_operations
        
        # If we reach here, all nodes failed
        logger.error("Tutti i nodi sono irraggiungibili")
        return []
    
    def calculate_vote_value(self, curator, vote_percent, effective_vests=None, voting_power=9200):
        """Calculate vote value based on blockchain parameters, similar to the JS implementation."""
        try:
            # Step 1: Get dynamic global properties
            steem = Steem(node=self.node_urls['steem'])
            props = steem.get_dynamic_global_properties()
            
            # Step 2: Calculate SP/VESTS ratio
            total_vesting_fund_steem = float(props['total_vesting_fund_steem']['amount'])
            total_vesting_shares = float(props['total_vesting_shares']['amount'])
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
            reward_fund = self.get_reward_fund("post")
            
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
            price_info = self.get_current_median_history_price()
            
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
    
    def format_results(self, results, username=None):
        """Format results for display"""
        if not results:
            print("Nessun risultato trovato.")
            return
        
        # Prepare data for tabulation
        table_data = []
        for op in results:
            reward_amount = op.get('reward', 'N/A')
            comment_author = op.get('comment_author', 'N/A')
            comment_permlink = op.get('comment_permlink', 'N/A')
            timestamp = op.get('timestamp', 'N/A')
            
            # Vote info if available
            vote_info = op.get('vote_info', {})
            vote_weight = vote_info.get('weight', 'N/A') if vote_info else 'N/A'
            days_to_reward = op.get('days_to_reward', 'N/A')
            
            # Calculate estimated vote value if vote info is available
            estimated_value = 'N/A'
            if vote_info and username and isinstance(vote_weight, (int, float)):
                try:
                    vote_calc = self.calculate_vote_value(username, vote_weight)
                    if 'error' not in vote_calc:
                        estimated_value = f"${vote_calc['sbd_value']:.4f}"
                except Exception as e:
                    logger.debug(f"Error calculating vote value: {e}")
            
            table_data.append([
                timestamp,
                comment_author,
                comment_permlink[:25] + '...' if len(comment_permlink) > 25 else comment_permlink,
                reward_amount,
                vote_weight,
                f"{days_to_reward:.1f}" if isinstance(days_to_reward, (int, float)) else days_to_reward,
                estimated_value
            ])
        
        headers = ['Timestamp', 'Author', 'Permlink', 'Reward', 'Vote Weight', 'Days to Reward', 'Est. Value']
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
          # Summary statistics
        total_rewards = len(results)
        rewards_with_votes = len([op for op in results if 'vote_info' in op])
        
        print(f"\n=== STATISTICHE ===")
        print(f"Totale ricompense di curation: {total_rewards}")
        print(f"Ricompense con voto corrispondente: {rewards_with_votes}")
        print(f"Percentuale di match: {(rewards_with_votes/total_rewards*100):.1f}%" if total_rewards > 0 else "N/A")
    
    def analyze_curator(self, username="tasuboyz", days_back=7):
        """Analyze a curator's activity"""
        print(f"Analizzando l'attività di {username} negli ultimi {days_back} giorni...")
        print("Connessione ai nodi Steem...")
        
        results = self.get_user_votes_by_days_back(username, days_back)
        self.format_results(results, username)
    
    def get_reward_fund(self, fund_name="post"):
        for node_url in self.node_urls.get('steem'):
            if not self.ping_server(node_url):
                logger.error(f"Impossibile raggiungere il server: {node_url}")
                continue
        """Get reward fund information directly from the blockchain.
        
        Args:
            fund_name (str): Name of the reward fund, typically "post"
            
        Returns:
            dict: Reward fund data with relevant information
        """
        try:
            headers = {'Content-Type': 'application/json'}
            payload = {
                "jsonrpc": "2.0",
                "method": "condenser_api.get_reward_fund",
                "params": [fund_name],
                "id": 1
            }
            
            response = requests.post(node_url, json=payload, headers=headers, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                if 'result' in result:
                    # Convert amounts to a more usable format
                    reward_data = result['result']
                    return reward_data
                    
            logger.warning(f"Failed to get reward fund data from {node_url}")
            # self.switch_to_backup_node()
            return self.get_reward_fund(fund_name)  # Try again with new node
            
        except Exception as e:
            logger.error(f"Error getting reward fund: {str(e)}")
            # self.switch_to_backup_node()
            return self.get_reward_fund(fund_name)  # Try again with new node
    
    def get_current_median_history_price(self):
        for node_url in self.node_urls.get('steem'):
            if not self.ping_server(node_url):
                logger.error(f"Impossibile raggiungere il server: {node_url}")
                continue
        """Get the current median price history from the blockchain.
        
        Returns:
            dict: Price data with base and quote values
        """
        try:
            headers = {'Content-Type': 'application/json'}
            payload = {
                "jsonrpc": "2.0",
                "method": "condenser_api.get_current_median_history_price",
                "params": [],
                "id": 1
            }
            
            response = requests.post(node_url, json=payload, headers=headers, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                if 'result' in result:
                    # Parse price data into a usable format
                    price_data = result['result']
                    
                    # Convert price strings to structured data
                    base_parts = price_data['base'].split(' ')
                    quote_parts = price_data['quote'].split(' ')
                    
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
                    
            logger.warning(f"Failed to get price data from {node_url}")
            # self.switch_to_backup_node()
            return self.get_current_median_history_price()  # Try again with new node
            
        except Exception as e:
            logger.error(f"Error getting current median history price: {str(e)}")
            # self.switch_to_backup_node()
            return self.get_current_median_history_price()  # Try again with new node

def main():
    """Main application entry point"""
    analyzer = CuratorAnalyzer()
    
    print("=== ANALIZZATORE CURATOR STEEM ===")
    print("Curator di default: tasuboyz")
    print("Nodi utilizzati:")
    for node in analyzer.node_urls['steem']:
        print(f"  - {node}")
    print()
    
    # Analyze default curator
    analyzer.analyze_curator()
      # Interactive mode
    while True:
        print("\n" + "="*50)
        print("Opzioni disponibili:")
        print("1. Analizzare un curator (inserisci username)")
        print("2. Testare calcolo valore voto (inserisci 'vote:username')")
        print("3. Uscire (inserisci 'exit' o 'n')")
        
        choice = input("\nInserisci la tua scelta: ").strip()
        
        if choice.lower() in ['n', 'no', 'exit', 'quit']:
            break
        elif choice.lower().startswith('vote:'):
            # Vote value calculation test
            username = choice.split(':', 1)[1].strip() if ':' in choice else 'tasuboyz'
        elif choice.lower() in ['s', 'si', 'yes', '']:
            username = input("Inserisci username del curator: ").strip()
            if username:
                days = input("Giorni da analizzare (default 7): ").strip()
                days_back = int(days) if days.isdigit() else 7
                analyzer.analyze_curator(username, days_back)
        else:
            # Assume the input is a username
            days = input("Giorni da analizzare (default 7): ").strip()
            days_back = int(days) if days.isdigit() else 7
            analyzer.analyze_curator(choice, days_back)

if __name__ == "__main__":
    main()