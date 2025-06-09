# -*- coding: utf-8 -*-
"""
Curator Analyzer
Main class that coordinates all services for curator analysis
"""

import logging
from typing import List, Dict, Any, Optional

from network.steem_connector import SteemConnector
from services.curator_service import CuratorService
from services.vote_calculator import VoteCalculator
from utils.formatters import ResultFormatter
from config.settings import DEFAULT_USERNAME, DEFAULT_DAYS_BACK, STEEM_NODES

logger = logging.getLogger(__name__)


class CuratorAnalyzer:
    """Main analyzer class that coordinates all services"""
    
    def __init__(self, node_urls: Optional[List[str]] = None):
        self.node_urls = node_urls or STEEM_NODES
        self.connector = SteemConnector(self.node_urls)
        self.curator_service = CuratorService(self.connector)
        self.vote_calculator = VoteCalculator(self.connector)
        self.formatter = ResultFormatter()
    
    def analyze_curator(self, username: str = DEFAULT_USERNAME, days_back: int = DEFAULT_DAYS_BACK) -> None:
        """
        Analyze a curator's activity and display results
        
        Args:
            username: Username of the curator to analyze
            days_back: Number of days to look back for analysis
        """
        self.formatter.display_analysis_header(username, days_back, self.node_urls)
        
        results = self.curator_service.get_user_votes_by_days_back(username, days_back)
        self.formatter.format_results(results, username)
    
    def get_curator_data(self, username: str, days_back: int = DEFAULT_DAYS_BACK) -> List[Dict[str, Any]]:
        """
        Get curator data without displaying it
        
        Args:
            username: Username of the curator to analyze
            days_back: Number of days to look back for analysis
            
        Returns:
            List of curator operations data
        """
        return self.curator_service.get_user_votes_by_days_back(username, days_back)
    
    def calculate_vote_value(
        self, 
        curator: str, 
        vote_percent: int, 
        effective_vests: Optional[float] = None, 
        voting_power: int = 9200
    ) -> Dict[str, Any]:
        """
        Calculate vote value for given parameters
        
        Args:
            curator: Username of the curator
            vote_percent: Vote weight percentage
            effective_vests: Optional effective vesting shares
            voting_power: Voting power (default 9200)
            
        Returns:
            Dictionary with calculated vote value data
        """
        return self.vote_calculator.calculate_vote_value(
            curator, vote_percent, effective_vests, voting_power
        )
    
    def test_connection(self) -> bool:
        """Test if connection to Steem network is working"""
        steem = self.connector.get_steem_instance()
        return steem is not None
    
    def get_working_nodes(self) -> List[str]:
        """Get list of currently working nodes"""
        working_nodes = []
        for node in self.node_urls:
            if self.connector.ping_server(node):
                working_nodes.append(node)
        return working_nodes
