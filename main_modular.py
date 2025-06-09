# -*- coding: utf-8 -*-
"""
Steem Curator Analyzer - Main Entry Point
Modular version with clean separation of concerns
"""

import logging
import sys
import os

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.analyzer import CuratorAnalyzer
from src.config.settings import LOGGING_LEVEL, LOG_FORMAT, DEFAULT_USERNAME

# Configure logging
logging.basicConfig(level=LOGGING_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


def main():
    """Main application entry point"""
    try:
        analyzer = CuratorAnalyzer()
        
        # Test connection first
        if not analyzer.test_connection():
            print("❌ Errore: Impossibile connettersi ai nodi Steem")
            return
        
        print("✅ Connessione ai nodi Steem stabilita")
        print(f"Nodi funzionanti: {analyzer.get_working_nodes()}")
        print()
        
        # Analyze default curator
        analyzer.analyze_curator()
        
        # Interactive mode
        interactive_mode(analyzer)
        
    except KeyboardInterrupt:
        print("\n\n👋 Uscita dal programma...")
    except Exception as e:
        logger.error(f"Errore critico: {e}")
        print(f"❌ Errore critico: {e}")


def interactive_mode(analyzer: CuratorAnalyzer):
    """Interactive mode for user input"""
    while True:
        print("\n" + "=" * 50)
        print("Opzioni disponibili:")
        print("1. Analizzare un curator (inserisci username)")
        print("2. Testare calcolo valore voto (inserisci 'vote:username:weight')")
        print("3. Mostrare nodi funzionanti (inserisci 'nodes')")
        print("4. Uscire (inserisci 'exit', 'quit' o 'n')")
        
        choice = input("\nInserisci la tua scelta: ").strip()
        
        if choice.lower() in ['n', 'no', 'exit', 'quit']:
            break
        elif choice.lower() == 'nodes':
            working_nodes = analyzer.get_working_nodes()
            print(f"\n🌐 Nodi funzionanti ({len(working_nodes)}):")
            for node in working_nodes:
                print(f"  ✅ {node}")
        elif choice.lower().startswith('vote:'):
            handle_vote_calculation(analyzer, choice)
        elif choice.lower() in ['s', 'si', 'yes', '']:
            handle_curator_analysis(analyzer)
        else:
            # Assume the input is a username
            handle_curator_analysis(analyzer, choice)


def handle_vote_calculation(analyzer: CuratorAnalyzer, choice: str):
    """Handle vote value calculation"""
    try:
        parts = choice.split(':')
        username = parts[1].strip() if len(parts) > 1 else DEFAULT_USERNAME
        weight = int(parts[2]) if len(parts) > 2 else 10000
        
        print(f"\n🧮 Calcolando valore voto per {username} con peso {weight}...")
        result = analyzer.calculate_vote_value(username, weight)
        
        if 'error' in result:
            print(f"❌ Errore nel calcolo: {result['error']}")
        else:
            print(f"💰 Valore stimato: {result['steem_value']:.4f} STEEM (${result['sbd_value']:.4f})")
            
    except (ValueError, IndexError) as e:
        print(f"❌ Formato non valido. Usa: vote:username:peso (es. vote:tasuboyz:5000)")


def handle_curator_analysis(analyzer: CuratorAnalyzer, username: str = None):
    """Handle curator analysis"""
    if not username:
        username = input("Inserisci username del curator: ").strip()
    
    if username:
        days_input = input("Giorni da analizzare (default 7): ").strip()
        days_back = int(days_input) if days_input.isdigit() else 7
        
        print(f"\n📊 Analizzando {username} per {days_back} giorni...")
        analyzer.analyze_curator(username, days_back)


if __name__ == "__main__":
    main()
