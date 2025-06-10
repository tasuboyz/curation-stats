# -*- coding: utf-8 -*-
"""
Feature Extractor for ML Models
Extracts features from curator data using rshares-based voter classification
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class VoterFeatureExtractor:
    """Estrae features dai votatori basandosi sui rshares"""
    
    def __init__(self):
        # Soglie per classificare i votatori
        self.whale_threshold = 1000000000  # 1B rshares = whale
        self.dolphin_threshold = 100000000  # 100M rshares = dolphin  
        self.minnow_threshold = 10000000   # 10M rshares = minnow
    
    def extract_voter_features(self, active_votes: List[Dict]) -> Dict[str, Any]:
        """
        Estrae features dai votatori basandosi sui rshares
        
        Args:
            active_votes: Lista dei voti attivi ordinati per rshares decrescente
            
        Returns:
            Dict con features sui votatori
        """
        if not active_votes:
            return self._get_empty_voter_features()
        
        # Classifica votatori per rshares
        whales = [v for v in active_votes if v.get('rshares', 0) >= self.whale_threshold]
        dolphins = [v for v in active_votes if self.dolphin_threshold <= v.get('rshares', 0) < self.whale_threshold]
        minnows = [v for v in active_votes if self.minnow_threshold <= v.get('rshares', 0) < self.dolphin_threshold]
        others = [v for v in active_votes if v.get('rshares', 0) < self.minnow_threshold]
        
        # Features sui votatori principali
        top_voters = active_votes[:10]  # Top 10 votatori
        
        # Timing features (quando votano i whale)
        whale_times = self._extract_vote_times(whales)
        dolphin_times = self._extract_vote_times(dolphins)
        
        return {
            # Conteggi per categoria
            'whale_count': len(whales),
            'dolphin_count': len(dolphins),
            'minnow_count': len(minnows),
            'other_count': len(others),
            'total_voters': len(active_votes),
            
            # Rshares totali per categoria
            'whale_total_rshares': sum(v.get('rshares', 0) for v in whales),
            'dolphin_total_rshares': sum(v.get('rshares', 0) for v in dolphins),
            'total_rshares': sum(v.get('rshares', 0) for v in active_votes),
            
            # Primo whale voter (il più importante)
            'first_whale_rshares': whales[0].get('rshares', 0) if whales else 0,
            'first_whale_time': whale_times[0] if whale_times else None,
            'first_whale_voter': whales[0].get('voter', '') if whales else '',
            
            # Distribuzione temporale delle whale
            'whale_earliest_time': min(whale_times) if whale_times else None,
            'whale_latest_time': max(whale_times) if whale_times else None,
            'whale_time_spread': (max(whale_times) - min(whale_times)) if len(whale_times) > 1 else 0,
            'whale_median_time': np.median(whale_times) if whale_times else None,
            
            # Concentrazione del potere di voto
            'whale_dominance': sum(v.get('rshares', 0) for v in whales) / max(1, sum(v.get('rshares', 0) for v in active_votes)),
            'top3_dominance': sum(v.get('rshares', 0) for v in active_votes[:3]) / max(1, sum(v.get('rshares', 0) for v in active_votes)),
            
            # Opportunità di front-running
            'front_run_opportunity': whale_times[0] > 1.0 if whale_times else False,  # Se il primo whale vota dopo 1 min
            'optimal_vote_window': max(0.5, whale_times[0] - 0.3) if whale_times else 5.0,  # Tempo ottimale stimato
            
            # Diversity metrics
            'voter_diversity_score': len(set(v.get('voter', '') for v in active_votes)),
            'unique_whale_voters': len(set(v.get('voter', '') for v in whales)),
        }
    
    def _extract_vote_times(self, votes: List[Dict]) -> List[float]:
        """Estrae i tempi di voto dai votatori"""
        times = []
        for vote in votes:
            # Assumiamo che il tempo sia già calcolato in minuti dal post
            time = vote.get('vote_delay_minutes')
            if time is not None:
                times.append(float(time))
        return sorted(times)
    
    def _get_empty_voter_features(self) -> Dict[str, Any]:
        """Ritorna features vuote quando non ci sono votatori"""
        return {
            'whale_count': 0,
            'dolphin_count': 0,
            'minnow_count': 0,
            'other_count': 0,
            'total_voters': 0,
            'whale_total_rshares': 0,
            'dolphin_total_rshares': 0,
            'total_rshares': 0,
            'first_whale_rshares': 0,
            'first_whale_time': None,
            'first_whale_voter': '',
            'whale_earliest_time': None,
            'whale_latest_time': None,
            'whale_time_spread': 0,
            'whale_median_time': None,
            'whale_dominance': 0,
            'top3_dominance': 0,
            'front_run_opportunity': False,
            'optimal_vote_window': 5.0,
            'voter_diversity_score': 0,
            'unique_whale_voters': 0,
        }


class CuratorMLFeatureExtractor:
    """Estrae features complete per modelli ML"""
    
    def __init__(self):
        self.voter_extractor = VoterFeatureExtractor()
    
    def extract_features_from_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estrae tutte le features da un record di curator data
        
        Args:
            record: Record dal curator service
            
        Returns:
            Dict con tutte le features per ML
        """
        features = {}
        
        # Features temporali
        features.update(self._extract_temporal_features(record))
        
        # Features del voto
        features.update(self._extract_vote_features(record))
        
        # Features dai votatori (basate su rshares)
        active_votes = record.get('active_votes', [])
        if active_votes:
            # Aggiungi timing ai voti se non presente
            active_votes = self._add_vote_timing(active_votes, record)
            features.update(self.voter_extractor.extract_voter_features(active_votes))
        else:
            features.update(self.voter_extractor._get_empty_voter_features())
        
        # Features di performance
        features.update(self._extract_performance_features(record))
        
        # Target variable (efficienza)
        features['efficiency_target'] = record.get('efficiency', 0) or 0
        
        return features
    
    def _extract_temporal_features(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Estrae features temporali"""
        timestamp = record.get('timestamp', '')
        voted_after_minutes = record.get('voted_after_minutes', 0) or 0
        
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            hour = dt.hour
            day_of_week = dt.weekday()
        except:
            hour = 12  # Default
            day_of_week = 1  # Default
        
        return {
            'voted_after_minutes': voted_after_minutes,
            'hour_of_day': hour,
            'day_of_week': day_of_week,
            'is_weekend': day_of_week >= 5,
            'is_prime_time': 18 <= hour <= 22,  # Prime time posting
        }
    
    def _extract_vote_features(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Estrae features del voto del curator"""
        vote_info = record.get('vote_info', {})
        
        return {
            'vote_weight': vote_info.get('weight', 0) or 0,
            'vote_weight_percent': (vote_info.get('weight', 0) or 0) / 100,
            'is_full_vote': (vote_info.get('weight', 0) or 0) >= 9000,  # 90%+ considerato full vote
        }
    
    def _extract_performance_features(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Estrae features di performance"""
        reward_sp = record.get('reward_sp', 0) or 0
        vote_value_steem = record.get('vote_value_steem', 0) or 0
        
        return {
            'reward_sp': reward_sp,
            'vote_value_steem': vote_value_steem,
            'has_reward_data': reward_sp > 0,
        }
    
    def _add_vote_timing(self, active_votes: List[Dict], record: Dict[str, Any]) -> List[Dict]:
        """Aggiunge timing approssimativo ai voti se non presente"""
        # Per ora usiamo un timing fittizio basato sull'ordine
        # In futuro si potrebbe migliorare con dati reali
        
        enriched_votes = []
        for i, vote in enumerate(active_votes):
            vote_copy = vote.copy()
            if 'vote_delay_minutes' not in vote_copy:
                # Timing fittizio: prime whale votano prima
                rshares = vote.get('rshares', 0)
                if rshares >= 1000000000:  # Whale
                    vote_copy['vote_delay_minutes'] = 1.0 + (i * 0.5)  # 1-5 minuti
                elif rshares >= 100000000:  # Dolphin
                    vote_copy['vote_delay_minutes'] = 3.0 + (i * 1.0)  # 3-10 minuti
                else:  # Others
                    vote_copy['vote_delay_minutes'] = 5.0 + (i * 2.0)  # 5+ minuti
            
            enriched_votes.append(vote_copy)
        
        return enriched_votes
    
    def create_dataset_from_curator_data(self, curator_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Crea un dataset pandas da una lista di record del curator
        
        Args:
            curator_data: Lista di record dal curator service
            
        Returns:
            DataFrame pandas con features per ML
        """
        features_list = []
        
        for record in curator_data:
            try:
                features = self.extract_features_from_record(record)
                features_list.append(features)
            except Exception as e:
                logger.warning(f"Errore nell'estrazione features: {e}")
                continue
        
        if not features_list:
            logger.warning("Nessuna feature estratta dai dati")
            return pd.DataFrame()
        
        df = pd.DataFrame(features_list)
        
        # Riempi valori mancanti
        df = df.fillna({
            'whale_earliest_time': 5.0,
            'whale_latest_time': 5.0,
            'whale_median_time': 5.0,
            'first_whale_time': 5.0,
            'optimal_vote_window': 5.0,
        })
        
        logger.info(f"Dataset creato: {len(df)} record, {len(df.columns)} features")
        return df


def analyze_dataset_quality(df: pd.DataFrame) -> Dict[str, Any]:
    """Analizza la qualità del dataset"""
    if df.empty:
        return {'error': 'Dataset vuoto'}
    
    # Analisi base
    total_records = len(df)
    records_with_whales = len(df[df['whale_count'] > 0])
    records_with_efficiency = len(df[df['efficiency_target'] > 0])
    
    # Distribuzione efficienza
    efficiency_stats = df['efficiency_target'].describe()
    
    # Features più importanti
    numeric_features = df.select_dtypes(include=[np.number]).columns
    feature_variance = df[numeric_features].var().sort_values(ascending=False)
    
    return {
        'total_records': total_records,
        'records_with_whales': records_with_whales,
        'whale_percentage': (records_with_whales / total_records) * 100,
        'records_with_efficiency': records_with_efficiency,
        'efficiency_percentage': (records_with_efficiency / total_records) * 100,
        'efficiency_stats': efficiency_stats.to_dict(),
        'top_variable_features': feature_variance.head(10).to_dict(),
        'missing_data_percentage': (df.isnull().sum() / len(df) * 100).to_dict()
    }
