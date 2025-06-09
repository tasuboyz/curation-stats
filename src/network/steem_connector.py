# -*- coding: utf-8 -*-
"""
Steem Network Connector
Handles connections to Steem blockchain nodes with failover support
"""

import logging
import requests
from typing import Optional, Dict, Any
from beem import Steem
from beem.account import Account

from config.settings import STEEM_NODES, DEFAULT_TIMEOUT

logger = logging.getLogger(__name__)


class SteemConnector:
    """Manages connections to Steem blockchain nodes"""
    
    def __init__(self, node_urls: Optional[list] = None):
        self.node_urls = node_urls or STEEM_NODES
        self.current_node = None
        self.steem_instance = None
    
    def ping_server(self, url: str) -> bool:
        """Test if server is reachable"""
        try:
            response = requests.get(url, timeout=DEFAULT_TIMEOUT)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_working_node(self) -> Optional[str]:
        """Find the first working node"""
        for node_url in self.node_urls:
            if self.ping_server(node_url):
                return node_url
            logger.error(f"Impossibile raggiungere il server: {node_url}")
        return None
    
    def get_steem_instance(self) -> Optional[Steem]:
        """Get a working Steem instance"""
        if self.steem_instance and self.current_node:
            return self.steem_instance
            
        working_node = self.get_working_node()
        if working_node:
            self.current_node = working_node
            self.steem_instance = Steem(node=working_node)
            return self.steem_instance
        
        logger.error("Tutti i nodi sono irraggiungibili")
        return None
    
    def get_account(self, username: str) -> Optional[Account]:
        """Get account information"""
        steem = self.get_steem_instance()
        if steem:
            try:
                return Account(username, blockchain_instance=steem)
            except Exception as e:
                logger.error(f"Error getting account {username}: {e}")
        return None
    
    def make_api_call(self, method: str, params: list = None) -> Optional[Dict[Any, Any]]:
        """Make a direct API call to Steem node"""
        working_node = self.get_working_node()
        if not working_node:
            return None
            
        try:
            headers = {'Content-Type': 'application/json'}
            payload = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params or [],
                "id": 1
            }
            
            response = requests.post(
                working_node, 
                json=payload, 
                headers=headers, 
                timeout=DEFAULT_TIMEOUT
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'result' in result:
                    return result['result']
                    
            logger.warning(f"Failed API call {method} on {working_node}")
            return None
            
        except Exception as e:
            logger.error(f"Error making API call {method}: {e}")
            return None
