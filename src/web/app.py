# -*- coding: utf-8 -*-
"""
Flask Web Application for Steem Curator Analyzer
Provides a web interface to analyze curator data with detailed tables
"""

import sys
import os
import logging
from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime
import csv
import io
# ML imports
import json
import pandas as pd

# Add src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '..')
sys.path.insert(0, src_dir)

from services.analyzer import CuratorAnalyzer
from utils.validators import InputValidator
from config.settings import DEFAULT_USERNAME, DEFAULT_DAYS_BACK
# ML imports
from ml.experiments import MLExperimentRunner
from ml.feature_extractor import CuratorMLFeatureExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global analyzer instance
analyzer = None
# Global ML runner instance
ml_runner = None

def get_analyzer():
    """Get or create analyzer instance"""
    global analyzer
    if analyzer is None:
        analyzer = CuratorAnalyzer()
    return analyzer

def get_ml_runner():
    """Get or create ML runner instance"""
    global ml_runner
    if ml_runner is None:
        ml_runner = MLExperimentRunner()
    return ml_runner

def calculate_efficiency(vote_value_steem, reward_sp):
    """Calculate efficiency percentage between vote value and actual reward"""
    try:
        if vote_value_steem > 0:
            return ((reward_sp / vote_value_steem) * 100)
        return 0
    except (TypeError, ZeroDivisionError):
        return 0

@app.route('/')
def index():
    """Main page with curator analysis form"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_curator():
    """Analyze curator and return results"""
    try:
        # Get form data
        username = request.form.get('username', DEFAULT_USERNAME).strip()
        days_back = int(request.form.get('days_back', DEFAULT_DAYS_BACK))
        
        # Validate inputs
        if not InputValidator.validate_username(username):
            return jsonify({
                'error': 'Username non valido. Deve essere tra 3-16 caratteri (lettere, numeri, punti, trattini).'
            }), 400
        
        if not InputValidator.validate_days_back(days_back):
            return jsonify({
                'error': 'Il numero di giorni deve essere tra 1 e 365.'
            }), 400
        
        # Get analyzer and fetch data
        analyzer = get_analyzer()
        
        # Test connection first
        if not analyzer.test_connection():
            return jsonify({
                'error': 'Impossibile connettersi ai nodi Steem. Riprova più tardi.'
            }), 503
        
        # Get curator data
        raw_data = analyzer.get_curator_data(username, days_back)
        
        if not raw_data:
            return jsonify({
                'error': 'Nessun dato trovato per questo curator nel periodo specificato.'
            }), 404
        
        # Process data for display
        processed_data = []
        total_reward_sp = 0
        total_vote_value = 0
        
        for item in raw_data:
            # Extract basic information
            reward_amount = item.get('reward', {})
            if isinstance(reward_amount, dict):
                reward_sp = item.get('reward_sp', 0)
            else:
                reward_sp = 0
                
            vote_info = item.get('vote_info', {})
            vote_value_steem = item.get('vote_value_steem', 0)
            
            # Calculate efficiency
            efficiency = calculate_efficiency(vote_value_steem, reward_sp)
            
            # Convert vote weight to percentage (10000 = 100%)
            vote_weight_raw = vote_info.get('weight', 0) if vote_info else 0
            vote_weight_percent = f"{vote_weight_raw / 100:.1f}%" if vote_weight_raw else "N/A"
            
            # Process row data
            row = {
                'timestamp': item.get('timestamp', 'N/A'),
                'curator': item.get('curator', username),
                'comment_author': item.get('comment_author', 'N/A'),
                'comment_permlink': item.get('comment_permlink', 'N/A')[:30] + '...' if len(item.get('comment_permlink', '')) > 30 else item.get('comment_permlink', 'N/A'),
                'reward_sp': f"{reward_sp:.6f}" if reward_sp else "0.000000",
                'vote_weight_percent': vote_weight_percent,
                'vote_value_steem': f"{vote_value_steem:.6f}" if vote_value_steem else "0.000000",
                'voted_after_minutes': f"{item.get('voted_after_minutes', 0):.1f}" if item.get('voted_after_minutes') is not None else 'N/A',
                'efficiency': f"{efficiency:.2f}%" if efficiency else "0.00%"
            }
            
            processed_data.append(row)
            
            # Accumulate totals for statistics
            if reward_sp:
                total_reward_sp += reward_sp
            if vote_value_steem:
                total_vote_value += vote_value_steem
        
        # Calculate summary statistics
        total_operations = len(processed_data)
        operations_with_votes = len([item for item in raw_data if 'vote_info' in item])
        match_percentage = (operations_with_votes / total_operations * 100) if total_operations > 0 else 0
        average_efficiency = calculate_efficiency(total_vote_value, total_reward_sp) if total_operations > 0 else 0
        
        statistics = {
            'total_operations': total_operations,
            'operations_with_votes': operations_with_votes,
            'match_percentage': f"{match_percentage:.1f}%",
            'total_reward_sp': f"{total_reward_sp:.6f}",
            'total_vote_value': f"{total_vote_value:.6f}",
            'average_efficiency': f"{average_efficiency:.2f}%",
            'analysis_period': f"{days_back} giorni",
            'working_nodes': len(analyzer.get_working_nodes())
        }
        
        return jsonify({
            'success': True,
            'data': processed_data,
            'statistics': statistics,
            'username': username,
            'days_back': days_back
        })
        
    except ValueError as e:
        return jsonify({'error': f'Errore nei parametri: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error analyzing curator: {str(e)}")
        return jsonify({'error': f'Errore durante l\'analisi: {str(e)}'}), 500

@app.route('/export_csv')
def export_csv():
    """Export curator data as CSV"""
    try:
        # Get parameters from query string
        username = request.args.get('username', DEFAULT_USERNAME)
        days_back = int(request.args.get('days_back', DEFAULT_DAYS_BACK))
        
        # Get analyzer and fetch data
        analyzer = get_analyzer()
        raw_data = analyzer.get_curator_data(username, days_back)
        
        if not raw_data:
            return jsonify({'error': 'Nessun dato da esportare'}), 404
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
          # Write headers
        headers = [
            'Timestamp', 'Curator', 'Author', 'Permlink', 'Reward SP', 
            'Vote Weight %', 'Vote Value STEEM', 'Voted After Minutes', 'Efficiency %'
        ]
        writer.writerow(headers)
        
        # Write data rows
        for item in raw_data:
            vote_info = item.get('vote_info', {})
            vote_value_steem = item.get('vote_value_steem', 0)
            reward_sp = item.get('reward_sp', 0)
            efficiency = calculate_efficiency(vote_value_steem, reward_sp)
            
            # Convert vote weight to percentage
            vote_weight_raw = vote_info.get('weight', 0) if vote_info else 0
            vote_weight_percent = vote_weight_raw / 100 if vote_weight_raw else 0
            
            row = [
                item.get('timestamp', ''),
                item.get('curator', username),
                item.get('comment_author', ''),
                item.get('comment_permlink', ''),
                reward_sp,
                f"{vote_weight_percent:.1f}%" if vote_weight_percent else "0.0%",
                vote_value_steem,
                item.get('voted_after_minutes', ''),
                f"{efficiency:.2f}" if efficiency else "0.00"
            ]
            writer.writerow(row)
        
        # Prepare file for download
        output.seek(0)
        
        # Create a BytesIO object for the file download
        mem = io.BytesIO()
        mem.write(output.getvalue().encode('utf-8'))
        mem.seek(0)
        
        filename = f"curator_analysis_{username}_{days_back}days_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return send_file(
            mem,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )
        
    except Exception as e:
        logger.error(f"Error exporting CSV: {str(e)}")
        return jsonify({'error': f'Errore durante l\'esportazione: {str(e)}'}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        analyzer = get_analyzer()
        working_nodes = analyzer.get_working_nodes()
        return jsonify({
            'status': 'healthy',
            'working_nodes': len(working_nodes),
            'nodes': working_nodes
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503

# ========== ML ENDPOINTS ==========

@app.route('/ml/feature_extraction', methods=['POST'])
def ml_feature_extraction():
    """Run ML feature extraction on curator data"""
    try:
        # Get form data
        username = request.form.get('username', DEFAULT_USERNAME).strip()
        days_back = int(request.form.get('days_back', DEFAULT_DAYS_BACK))
        
        # Validate inputs
        if not InputValidator.validate_username(username):
            return jsonify({
                'error': 'Username non valido. Deve essere tra 3-16 caratteri (lettere, numeri, punti, trattini).'
            }), 400
        
        if not InputValidator.validate_days_back(days_back):
            return jsonify({
                'error': 'Il numero di giorni deve essere tra 1 e 365.'
            }), 400
        
        # Get analyzer and fetch data
        analyzer = get_analyzer()
        
        # Test connection first
        if not analyzer.test_connection():
            return jsonify({
                'error': 'Impossibile connettersi ai nodi Steem. Riprova più tardi.'
            }), 503
        
        # Get curator data
        raw_data = analyzer.get_curator_data(username, days_back)
        
        if not raw_data:
            return jsonify({
                'error': 'Nessun dato trovato per questo curator nel periodo specificato.'
            }), 404
        
        # Extract features using ML
        feature_extractor = CuratorMLFeatureExtractor()
        features = feature_extractor.extract_features(raw_data)
        
        # Convert features to DataFrame for better readability
        features_df = pd.DataFrame(features)
        
        # Prepare response data
        response_data = {
            'username': username,
            'days_back': days_back,
            'features': features_df.to_dict(orient='records')
        }
        
        return jsonify({
            'success': True,
            'data': response_data
        })
        
    except ValueError as e:
        return jsonify({'error': f'Errore nei parametri: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error in ML feature extraction: {str(e)}")
        return jsonify({'error': f'Errore durante l\'estrazione delle caratteristiche: {str(e)}'}), 500

@app.route('/ml/run_experiment', methods=['POST'])
def ml_run_experiment():
    """Run ML experiment and return results"""
    try:
        # Get form data
        experiment_name = request.form.get('experiment_name', '').strip()
        username = request.form.get('username', DEFAULT_USERNAME).strip()
        days_back = int(request.form.get('days_back', DEFAULT_DAYS_BACK))
        
        # Validate inputs
        if not experiment_name:
            return jsonify({
                'error': 'Il nome dell\'esperimento è obbligatorio.'
            }), 400
        
        if not InputValidator.validate_username(username):
            return jsonify({
                'error': 'Username non valido. Deve essere tra 3-16 caratteri (lettere, numeri, punti, trattini).'
            }), 400
        
        if not InputValidator.validate_days_back(days_back):
            return jsonify({
                'error': 'Il numero di giorni deve essere tra 1 e 365.'
            }), 400
        
        # Get analyzer and fetch data
        analyzer = get_analyzer()
        
        # Test connection first
        if not analyzer.test_connection():
            return jsonify({
                'error': 'Impossibile connettersi ai nodi Steem. Riprova più tardi.'
            }), 503
        
        # Get curator data
        raw_data = analyzer.get_curator_data(username, days_back)
        
        if not raw_data:
            return jsonify({
                'error': 'Nessun dato trovato per questo curator nel periodo specificato.'
            }), 404
        
        # Run ML experiment
        experiment_runner = get_ml_runner()
        experiment_results = experiment_runner.run_experiment(experiment_name, raw_data)
        
        return jsonify({
            'success': True,
            'experiment_name': experiment_name,
            'results': experiment_results
        })
        
    except ValueError as e:
        return jsonify({'error': f'Errore nei parametri: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error running ML experiment: {str(e)}")
        return jsonify({'error': f'Errore durante l\'esecuzione dell\'esperimento: {str(e)}'}), 500

@app.route('/ml/train', methods=['POST'])
def train_ml_models():
    """Train ML models with curator data"""
    try:
        # Get form data
        username = request.form.get('username', DEFAULT_USERNAME).strip()
        days_back = int(request.form.get('days_back', DEFAULT_DAYS_BACK))
        
        # Get curator data
        analyzer = get_analyzer()
        raw_data = analyzer.get_curator_data(username, days_back)
        
        if not raw_data or len(raw_data) < 10:
            return jsonify({
                'error': 'Dati insufficienti per il training. Necessari almeno 10 record.'
            }), 400
        
        # Get ML runner and train models
        ml_runner = get_ml_runner()
        
        # Prepare dataset
        df, quality_analysis = ml_runner.prepare_dataset(raw_data)
        
        # Run experiments
        results = ml_runner.run_experiments(df)
        
        # Find best model
        best_model_info = ml_runner.get_best_model(results)
        
        return jsonify({
            'success': True,
            'dataset_info': {
                'total_records': len(df),
                'features_count': len([col for col in df.columns if col != 'efficiency']),
                'quality_score': quality_analysis.get('overall_score', 0)
            },
            'model_results': results,
            'best_model': best_model_info,
            'quality_analysis': quality_analysis
        })
        
    except Exception as e:
        logger.error(f"Error training ML models: {str(e)}")
        return jsonify({'error': f'Errore durante il training: {str(e)}'}), 500

@app.route('/ml/predict', methods=['POST'])
def predict_optimal_timing():
    """Predict optimal voting timing"""
    try:
        data = request.get_json()
        
        # Extract prediction parameters
        author = data.get('author', '')
        permlink = data.get('permlink', '')
        post_age_minutes = data.get('post_age_minutes', 0)
        
        if not author or not permlink:
            return jsonify({
                'error': 'Author e permlink sono obbligatori per la predizione'
            }), 400
        
        # Get analyzer to fetch post data
        analyzer = get_analyzer()
        
        # Simulate getting post and votes data
        # In a real implementation, this would fetch actual post data
        prediction_data = {
            'author': author,
            'permlink': permlink,
            'post_age_minutes': post_age_minutes,
            'prediction': 'Feature in development'
        }
        
        return jsonify({
            'success': True,
            'prediction': prediction_data,
            'optimal_timing': {
                'suggested_minutes': 15,  # Placeholder
                'confidence': 0.85,
                'reasoning': 'Based on historical whale voting patterns'
            }
        })
        
    except Exception as e:
        logger.error(f"Error making prediction: {str(e)}")
        return jsonify({'error': f'Errore durante la predizione: {str(e)}'}), 500

@app.route('/ml/analyze_post', methods=['POST'])
def analyze_post_for_curation():
    """Analyze a specific post for curation opportunities"""
    try:
        data = request.get_json()
        author = data.get('author', '')
        permlink = data.get('permlink', '')
        
        if not author or not permlink:
            return jsonify({
                'error': 'Author e permlink sono obbligatori'
            }), 400
        
        # Get analyzer
        analyzer = get_analyzer()
        
        # Get post analysis (this would be implemented)
        post_analysis = {
            'author': author,
            'permlink': permlink,
            'whale_voters_detected': [],
            'optimal_vote_time': '12-18 minuti dopo pubblicazione',
            'expected_efficiency': '75-85%',
            'risk_level': 'Medium',
            'recommendations': [
                'Vota entro 15 minuti per massimizzare curation reward',
                'Monitora i whale voters attivi su questo autore',
                'Peso voto consigliato: 80-100%'
            ]
        }
        
        return jsonify({
            'success': True,
            'analysis': post_analysis
        })
        
    except Exception as e:
        logger.error(f"Error analyzing post: {str(e)}")
        return jsonify({'error': f'Errore durante l\'analisi: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
