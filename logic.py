def calculate_optimal_vote_time(self, voters_data, buffer_minutes=0.2, max_top_voters=8, consider_delayed_votes=True, min_vote_time=1.0, curator_username=None):
        """Calcola il tempo ottimale per votare in base ai votanti importanti
        
        Args:
            voters_data (list): Lista di dati sui votanti con 'importance' e 'vote_delay_minutes'
            buffer_minutes (float): Minuti di anticipo rispetto al primo votante importante
            max_top_voters (int): Numero massimo di votanti importanti da considerare
            consider_delayed_votes (bool): Se considerare anche votanti che votano oltre il primo minuto
            min_vote_time (float): Tempo minimo di voto in minuti, per evitare voti troppo precoci
            curator_username (str): Nome utente del curatore da escludere dal calcolo
            
        Returns:
            dict: Dizionario con 'optimal_time' (in minuti) e 'explanation'
        """
        # Ottieni il nome del curatore se non è fornito
        if not curator_username and hasattr(self, 'blockchain_connector'):
            try:
                platform = 'steem'  # Default, ma sarà lo stesso algoritmo per entrambe le piattaforme
                curator_info = self.blockchain_connector.get_curator_info(platform)
                curator_username = (curator_info.get('username') or '').lower()
            except Exception as e:
                logger.debug(f"Non è stato possibile ottenere il nome del curatore: {e}")
                curator_username = None
                
        # Filtra il curatore dai dati dei votanti se presente
        if curator_username:
            voters_data = [v for v in voters_data if v.get('voter', '').lower() != curator_username.lower()]
                
        if not voters_data:
            return {
                'optimal_time': 5,  # Default se non ci sono dati
                'explanation': 'Nessun dato sui votanti disponibile, usando il tempo predefinito di 5 minuti',
                'vote_window': (4.5, 5.5),  # Finestra di voto predefinita
                'voter_groups': {}
            }
        
        # Ordina i votanti per valore del voto in STEEM (decrescente)
        important_voters = sorted(voters_data, key=lambda x: x.get('steem_vote_value', 0) or 0, reverse=True)
        
        # Calcola dinamicamente il numero di top voters da considerare in base al loro valore
        # Conta quanti votanti hanno almeno 10 STEEM di valore
        default_top_count = 3
        high_value_voters = [v for v in important_voters if (v.get('steem_vote_value', 0) or 0) >= 10.0]
        num_high_value = len(high_value_voters)
        
        # Se ci sono votanti con almeno 10 STEEM, allarga la considerazione per includere almeno questi
        if num_high_value > 0:
            # Usa max_top_voters ma assicurati di includere almeno tutti quelli con alto valore
            effective_top_voters = max(num_high_value, min(max_top_voters, len(important_voters)))
        else:
            # Altrimenti usa solo il conteggio predefinito
            effective_top_voters = default_top_count
        
        logger.debug(f"Trovati {num_high_value} votanti con valore ≥ 10 STEEM, "
                     f"utilizzando {effective_top_voters} top voters su {len(important_voters)} totali")
        
        # Prendi un numero appropriato di votanti importanti, se disponibili
        top_voters = important_voters[:min(effective_top_voters, len(important_voters))]
        
        # Calcola il valore totale in STEEM di questi votanti
        total_steem_value = sum(v.get('steem_vote_value', 0) or 0 for v in top_voters)
        
        # Usa il valore tradizionale dell'importanza come fallback se non ci sono valori STEEM
        if total_steem_value <= 0:
            important_voters = sorted(voters_data, key=lambda x: x.get('importance', 0), reverse=True)
            top_voters = important_voters[:min(max_top_voters, len(important_voters))]
            total_importance = sum(v.get('importance', 0) for v in top_voters)
        else:
            total_importance = total_steem_value  # Usa il valore STEEM come importanza totale
        
        if total_importance <= 0:
            return {
                'optimal_time': 5,  # Default in caso di importanza zero
                'explanation': 'Importanza dei votanti troppo bassa, usando il tempo predefinito di 5 minuti',
                'vote_window': (4.5, 5.5),
                'voter_groups': {}
            }
          # NUOVA LOGICA: Trova il tempo del top voter più veloce e votalo prima
        # Ordinamento dei top_voters per tempo di voto (crescente), gestendo correttamente valori None
        top_voters_by_time = sorted(top_voters, key=lambda x: x.get('vote_delay_minutes') if x.get('vote_delay_minutes') is not None else 30)
        
        # Trova il primo votante tra i top_voters
        if top_voters_by_time:
            earliest_top_voter = top_voters_by_time[0]
            earliest_top_time = earliest_top_voter.get('vote_delay_minutes', 30)
            earliest_top_value = earliest_top_voter.get('steem_vote_value', 0) or earliest_top_voter.get('importance', 0)
            
            # Calcola il tempo ottimale: anticipa il primo top voter di buffer_minutes
            calculated_time = max(0.5, earliest_top_time - buffer_minutes)
            optimal_time = max(min_vote_time, calculated_time)
            
            # Costruisci la spiegazione
            if optimal_time == min_vote_time and calculated_time < min_vote_time:
                strategy_explanation = f"Anticipiamo tutti i top voters (primo: @{earliest_top_voter.get('voter', 'sconosciuto')}, {earliest_top_value:.3f} STEEM a {earliest_top_time} min), rispettando il tempo minimo di {min_vote_time} min."
            else:
                strategy_explanation = f"Anticipiamo tutti i top voters (primo: @{earliest_top_voter.get('voter', 'sconosciuto')}, {earliest_top_value:.3f} STEEM a {earliest_top_time} min)"
            
            # Finestra di voto più precisa per garantire di votare prima del primo top voter
            vote_window = (optimal_time - 0.1, optimal_time + 0.1)
            
            # Genera una spiegazione più dettagliata
            detailed_explanation = strategy_explanation + "\n"
            
            # Aggiungi dettagli sui top voters ordinati per tempo
            if len(top_voters_by_time) > 0:
                top_3_voters = top_voters_by_time[:min(3, len(top_voters_by_time))]
                voter_details = [f"@{v.get('voter', 'sconosciuto')} (valore: {v.get('steem_vote_value', 0) or v.get('importance', 0):.3f} STEEM, dopo {v.get('vote_delay_minutes', 0):.1f} min)" 
                                for v in top_3_voters]
                detailed_explanation += f"Top voters ordinati per tempo: {', '.join(voter_details)}"
                
                # Aggiungi anche dettagli sui top voters per valore
                top_3_value_voters = top_voters[:min(3, len(top_voters))]
                value_details = [f"@{v.get('voter', 'sconosciuto')} (valore: {v.get('steem_vote_value', 0) or v.get('importance', 0):.3f} STEEM, dopo {v.get('vote_delay_minutes', 0):.1f} min)" 
                                for v in top_3_value_voters]
                detailed_explanation += f"\nTop voters per valore: {', '.join(value_details)}"
            
            # Raggruppa i votanti per fasce temporali (per retrocompatibilità)
            immediate_voters = [v for v in top_voters if v.get('vote_delay_minutes', 30) <= 1]
            quick_voters = [v for v in top_voters if 1 < v.get('vote_delay_minutes', 30) <= 5]
            delayed_voters = [v for v in top_voters if v.get('vote_delay_minutes', 30) > 5]
            
            # Calcola l'importanza totale per ciascun gruppo
            immediate_importance = sum(v.get('steem_vote_value', 0) or v.get('importance', 0) for v in immediate_voters)
            quick_importance = sum(v.get('steem_vote_value', 0) or v.get('importance', 0) for v in quick_voters)
            delayed_importance = sum(v.get('steem_vote_value', 0) or v.get('importance', 0) for v in delayed_voters)
            
            # Prepara i gruppi di votanti per l'output
            voter_groups = {
                "immediate": [v.get('voter') for v in immediate_voters],
                "quick": [v.get('voter') for v in quick_voters],
                "delayed": [v.get('voter') for v in delayed_voters],
                "top_by_time": [v.get('voter') for v in top_voters_by_time[:min(3, len(top_voters_by_time))]]
            }
            
            # Formatta i valori di importance per i gruppi
            group_importance = {
                "immediate": round(immediate_importance, 3),
                "quick": round(quick_importance, 3),
                "delayed": round(delayed_importance, 3)
            }
            
            # Aggiungi informazione sui votanti di alto valore
            high_value_count = num_high_value
            high_value_info = f"{high_value_count} votanti con valore ≥ 10 STEEM" if high_value_count > 0 else "Nessun votante con alto valore"
            
            return {
                'optimal_time': round(optimal_time, 1),
                'explanation': detailed_explanation,
                'strategy': strategy_explanation,
                'top_voters': [v.get('voter', 'sconosciuto') for v in top_voters[:min(5, len(top_voters))]],
                'vote_window': (round(vote_window[0], 1), round(vote_window[1], 1)),
                'voter_groups': voter_groups,
                'group_importance': group_importance,
                'high_value_info': high_value_info,
                'high_value_count': high_value_count,
                'earliest_top_voter': earliest_top_voter.get('voter', 'sconosciuto'),
                'earliest_top_time': earliest_top_time
            }
        else:
            # Nessun votante significativo trovato
            return {
                'optimal_time': 5,
                'explanation': 'Nessun votante significativo trovato, usando il tempo predefinito di 5 minuti',
                'vote_window': (4.5, 5.5),
                'voter_groups': {}
            }