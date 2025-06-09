# -*- coding: utf-8 -*-
"""
Configuration settings for Steem Curator Analyzer
"""

import logging
from typing import List, Dict

# Logging configuration
LOGGING_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Steem node URLs
STEEM_NODES: List[str] = [
    "https://api.moecki.online",
    "https://api.steemit.com", 
    "https://api.justyy.com"
]

# Default values
DEFAULT_USERNAME = "tasuboyz"
DEFAULT_DAYS_BACK = 7
DEFAULT_VOTING_POWER = 9200
DEFAULT_BATCH_SIZE = 500
DEFAULT_TIMEOUT = 5

# Analysis parameters
VOTE_BUFFER_DAYS = 14  # Extra days to look back for votes (rewards come ~7 days after votes)

# Table formatting
TABLE_FORMAT = 'grid'
MAX_PERMLINK_LENGTH = 25

# API endpoints
API_ENDPOINTS = {
    'reward_fund': 'condenser_api.get_reward_fund',
    'median_price': 'condenser_api.get_current_median_history_price'
}

# Messages
MESSAGES = {
    'it': {
        'analyzing': "Analizzando l'attività di {username} negli ultimi {days} giorni...",
        'connecting': "Connessione ai nodi Steem...",
        'no_results': "Nessun risultato trovato.",
        'server_unreachable': "Impossibile raggiungere il server: {url}",
        'all_nodes_failed': "Tutti i nodi sono irraggiungibili",
        'statistics': "=== STATISTICHE ===",
        'total_rewards': "Totale ricompense di curation: {count}",
        'matched_rewards': "Ricompense con voto corrispondente: {count}",
        'match_percentage': "Percentuale di match: {percentage:.1f}%"
    }
}
