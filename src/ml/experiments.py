# -*- coding: utf-8 -*-
"""
ML Experiments for Curator Optimization
Sperimentazione di diversi modelli per ottimizzare i tempi di voto
"""

import logging
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, TimeSeriesSplit, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import lightgbm as lgb
from typing import Dict, List, Any, Tuple, Optional

from ml.feature_extractor import CuratorMLFeatureExtractor, analyze_dataset_quality

logger = logging.getLogger(__name__)


class MLExperimentRunner:
    """Runner per esperimenti di ML"""
    
    def __init__(self):
        self.feature_extractor = CuratorMLFeatureExtractor()
        self.scaler = StandardScaler()
        self.models = {}
        self.results = {}
    
    def prepare_dataset(self, curator_data: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Prepara il dataset per gli esperimenti
        
        Args:
            curator_data: Dati grezzi dal curator service
            
        Returns:
            Tuple con DataFrame e analisi qualità
        """
        print("🔄 Creazione dataset...")
        df = self.feature_extractor.create_dataset_from_curator_data(curator_data)
        
        if df.empty:
            raise ValueError("Dataset vuoto dopo l'estrazione features")
        
        # Analisi qualità
        quality_analysis = analyze_dataset_quality(df)
        
        print(f"📊 Dataset preparato:")
        print(f"  - Record totali: {quality_analysis['total_records']}")
        print(f"  - Record con whale: {quality_analysis['records_with_whales']} ({quality_analysis['whale_percentage']:.1f}%)")
        print(f"  - Record con efficienza: {quality_analysis['records_with_efficiency']} ({quality_analysis['efficiency_percentage']:.1f}%)")
        
        return df, quality_analysis
    
    def run_experiments(self, df: pd.DataFrame, target_column: str = 'efficiency_target') -> Dict[str, Any]:
        """
        Esegue esperimenti con diversi modelli
        
        Args:
            df: DataFrame con features
            target_column: Nome della colonna target
            
        Returns:
            Risultati degli esperimenti
        """
        # Filtra record con target validi
        valid_df = df[df[target_column] > 0].copy()
        
        if len(valid_df) < 10:
            raise ValueError(f"Troppo pochi record validi: {len(valid_df)}")
        
        print(f"🧪 Inizio esperimenti ML con {len(valid_df)} record validi...")
        
        # Prepara features e target
        X, y = self._prepare_features_target(valid_df, target_column)
        
        # Split train/test temporale
        X_train, X_test, y_train, y_test = self._temporal_split(X, y, test_size=0.2)
        
        # Normalizza features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Modelli da testare
        models_to_test = {
            'linear_regression': LinearRegression(),
            'ridge': Ridge(alpha=1.0),
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42),
            'lightgbm': lgb.LGBMRegressor(n_estimators=100, random_state=42, verbose=-1)
        }
        
        results = {}
        
        for model_name, model in models_to_test.items():
            print(f"  🔬 Testing {model_name}...")
            
            try:
                # Addestra modello
                if model_name == 'lightgbm':
                    model.fit(X_train, y_train)
                    y_pred = model.predict(X_test)
                else:
                    model.fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_test_scaled)
                
                # Calcola metriche
                mse = mean_squared_error(y_test, y_pred)
                rmse = np.sqrt(mse)
                mae = mean_absolute_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                
                # Cross-validation
                if model_name == 'lightgbm':
                    cv_scores = cross_val_score(model, X_train, y_train, cv=3, scoring='r2')
                else:
                    cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=3, scoring='r2')
                
                results[model_name] = {
                    'model': model,
                    'rmse': rmse,
                    'mae': mae,
                    'r2': r2,
                    'cv_mean': cv_scores.mean(),
                    'cv_std': cv_scores.std(),
                    'predictions': y_pred,
                    'actual': y_test
                }
                
                print(f"    ✅ R²: {r2:.3f}, RMSE: {rmse:.3f}, CV: {cv_scores.mean():.3f}±{cv_scores.std():.3f}")
                
            except Exception as e:
                print(f"    ❌ Errore con {model_name}: {e}")
                results[model_name] = {'error': str(e)}
        
        # Trova il miglior modello
        best_model = self._find_best_model(results)
        
        self.models = {name: res.get('model') for name, res in results.items() if 'model' in res}
        self.results = results
        
        return {
            'results': results,
            'best_model': best_model,
            'feature_names': list(X.columns),
            'dataset_info': {
                'total_records': len(valid_df),
                'train_size': len(X_train),
                'test_size': len(X_test),
                'features_count': len(X.columns)
            }
        }
    
    def _prepare_features_target(self, df: pd.DataFrame, target_column: str) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepara features e target per ML"""
        # Rimuovi colonne non utili
        exclude_columns = [
            target_column, 'first_whale_voter', 'timestamp',
            'comment_author', 'comment_permlink', 'curator'
        ]
        
        feature_columns = [col for col in df.columns if col not in exclude_columns]
        
        X = df[feature_columns].copy()
        y = df[target_column].copy()
        
        # Gestisci variabili categoriche se presenti
        categorical_columns = X.select_dtypes(include=['object']).columns
        for col in categorical_columns:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
        
        # Riempi NaN
        X = X.fillna(X.median())
        
        return X, y
    
    def _temporal_split(self, X: pd.DataFrame, y: pd.Series, test_size: float = 0.2) -> Tuple:
        """Split temporale per evitare data leakage"""
        split_idx = int(len(X) * (1 - test_size))
        
        X_train = X.iloc[:split_idx]
        X_test = X.iloc[split_idx:]
        y_train = y.iloc[:split_idx]
        y_test = y.iloc[split_idx:]
        
        return X_train, X_test, y_train, y_test
    
    def _find_best_model(self, results: Dict[str, Any]) -> str:
        """Trova il modello con le migliori performance"""
        best_model = None
        best_score = -float('inf')
        
        for name, result in results.items():
            if 'r2' in result and result['r2'] > best_score:
                best_score = result['r2']
                best_model = name
        
        return best_model
    
    def get_best_model(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ottiene informazioni sul miglior modello
        
        Args:
            results: Risultati degli esperimenti
            
        Returns:
            Informazioni sul miglior modello
        """
        best_model_name = self._find_best_model(results)
        
        if not best_model_name:
            return {
                'name': 'None',
                'r2_score': 0,
                'mse': float('inf'),
                'mae': float('inf')
            }
        
        best_result = results[best_model_name]
        
        return {
            'name': best_model_name.replace('_', ' ').title(),
            'r2_score': best_result.get('r2', 0),
            'mse': best_result.get('mse', float('inf')),
            'mae': best_result.get('mae', float('inf')),
            'training_time': best_result.get('training_time', 0)
        }
    
    def analyze_feature_importance(self, model_name: str = None) -> Dict[str, float]:
        """Analizza l'importanza delle features"""
        if model_name is None:
            model_name = self._find_best_model(self.results)
        
        if model_name not in self.models:
            return {}
        
        model = self.models[model_name]
        
        try:
            if hasattr(model, 'feature_importances_'):
                importance = model.feature_importances_
            elif hasattr(model, 'coef_'):
                importance = np.abs(model.coef_)
            else:
                return {}
            
            feature_names = self.results.get('feature_names', [])
            if len(feature_names) != len(importance):
                return {}
            
            return dict(zip(feature_names, importance))
            
        except Exception as e:
            logger.warning(f"Errore nel calcolo feature importance: {e}")
            return {}
    
    def predict_optimal_time(self, record: Dict[str, Any], model_name: str = None) -> Dict[str, Any]:
        """
        Predice il tempo ottimale per un nuovo record
        
        Args:
            record: Record con dati del post/votatori
            model_name: Nome del modello da usare
            
        Returns:
            Predizione con confidence
        """
        if model_name is None:
            model_name = self._find_best_model(self.results)
        
        if model_name not in self.models:
            return {'error': 'Modello non disponibile'}
        
        try:
            # Estrai features
            features = self.feature_extractor.extract_features_from_record(record)
            
            # Prepara per predizione
            feature_names = self.results.get('feature_names', [])
            X_pred = pd.DataFrame([features])[feature_names]
            X_pred = X_pred.fillna(X_pred.median())
            
            model = self.models[model_name]
            
            # Fai predizione
            if model_name == 'lightgbm':
                prediction = model.predict(X_pred)[0]
            else:
                X_pred_scaled = self.scaler.transform(X_pred)
                prediction = model.predict(X_pred_scaled)[0]
            
            # Converti da efficienza a tempo ottimale
            optimal_time = self._efficiency_to_optimal_time(prediction, features)
            
            return {
                'optimal_time': round(optimal_time, 1),
                'predicted_efficiency': round(prediction, 2),
                'model_used': model_name,
                'confidence': self._calculate_confidence(prediction, model_name)
            }
            
        except Exception as e:
            return {'error': f'Errore nella predizione: {e}'}
    
    def _efficiency_to_optimal_time(self, predicted_efficiency: float, features: Dict) -> float:
        """Converte efficienza predetta in tempo ottimale"""
        # Logica semplice: se ci sono whale, vota prima del primo whale
        if features.get('whale_count', 0) > 0 and features.get('first_whale_time'):
            # Anticipa il primo whale di 0.3 minuti
            optimal_time = max(0.5, features['first_whale_time'] - 0.3)
        else:
            # Default basato sull'efficienza predetta
            if predicted_efficiency > 80:
                optimal_time = 1.5  # Vota presto se alta efficienza attesa
            elif predicted_efficiency > 50:
                optimal_time = 3.0  # Vota moderatamente presto
            else:
                optimal_time = 5.0  # Vota normale
        
        return optimal_time
    
    def _calculate_confidence(self, prediction: float, model_name: str) -> float:
        """Calcola confidence della predizione"""
        if model_name not in self.results:
            return 0.5
        
        r2_score = self.results[model_name].get('r2', 0)
        cv_std = self.results[model_name].get('cv_std', 1.0)
        
        # Confidence basata su R² e stabilità CV
        confidence = r2_score * (1 - cv_std)
        return max(0.1, min(1.0, confidence))


def run_ml_experiment(curator_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Funzione principale per eseguire esperimenti ML
    
    Args:
        curator_data: Dati dal curator service
        
    Returns:
        Risultati completi degli esperimenti
    """
    print("🚀 Inizio esperimenti ML per ottimizzazione curator...")
    
    try:
        # Inizializza runner
        runner = MLExperimentRunner()
        
        # Prepara dataset
        df, quality_analysis = runner.prepare_dataset(curator_data)
        
        # Verifica qualità minima
        if quality_analysis['records_with_efficiency'] < 10:
            return {
                'error': 'Dataset insufficiente per ML',
                'quality_analysis': quality_analysis
            }
        
        # Esegui esperimenti
        experiment_results = runner.run_experiments(df)
        
        # Analizza feature importance
        feature_importance = runner.analyze_feature_importance()
        
        print("✅ Esperimenti completati!")
        print(f"🏆 Miglior modello: {experiment_results['best_model']}")
        
        return {
            'success': True,
            'quality_analysis': quality_analysis,
            'experiment_results': experiment_results,
            'feature_importance': feature_importance,
            'runner': runner  # Per predizioni future
        }
        
    except Exception as e:
        print(f"❌ Errore negli esperimenti: {e}")
        return {
            'error': str(e),
            'success': False
        }
