

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