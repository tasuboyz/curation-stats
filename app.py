# -*- coding: utf-8 -*-
"""
Main Flask Application Entry Point
Launches the Steem Curator Analyzer web interface
"""

import sys
import os

# Add src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# Import and run the Flask app
from src.web.app import app

if __name__ == '__main__':
    print("🚀 Avvio Steem Curator Analyzer Web Interface...")
    print("📊 Accedi a: http://localhost:5000")
    print("🔗 API Health Check: http://localhost:5000/health")
    print("📋 Premi Ctrl+C per fermare il server")
    print("-" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
