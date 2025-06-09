# Interfaccia Web - Steem Curator Analyzer

## 🌐 Avvio dell'Applicazione Web

### Metodo 1: File principale
```bash
python app.py
```

### Metodo 2: Direttamente dal modulo web
```bash
python src/web/app.py
```

## 📊 Funzionalità dell'Interfaccia Web

### 🏠 Pagina Principale (`/`)
- **Form di input** per inserire:
  - Username del curator (es. "tasuboyz")
  - Numero di giorni da analizzare (1-365)
- **Validazione automatica** degli input
- **Interfaccia responsive** con Bootstrap 5

### 📈 Analisi Dati (`/analyze`)
- **Elaborazione asincrona** dei dati
- **Indicatore di caricamento** durante l'analisi
- **Tabella dettagliata** con tutte le informazioni:
  - Timestamp del reward
  - Curator e autore del post
  - Permlink del post
  - Importo del reward
  - Reward in SP
  - Peso del voto
  - Valore stimato del voto
  - Minuti tra pubblicazione e voto
  - Giorni tra voto e reward
  - **Percentuale di efficienza** (reward_sp / vote_value_steem)
  - Numero del blocco

### 📊 Statistiche Riassuntive
- **Operazioni totali** trovate
- **Operazioni con voti** corrispondenti
- **Percentuale di match** voti-reward
- **Reward totale** in SP
- **Efficienza media** del curator

### 💾 Esportazione CSV (`/export_csv`)
- **Download automatico** del file CSV
- **Nome file** con timestamp: `curator_analysis_[username]_[days]days_[timestamp].csv`
- **Tutte le colonne** incluse per analisi esterne

### 🔍 Health Check (`/health`)
- **Stato dell'applicazione**
- **Nodi Steem funzionanti**
- **Endpoint per monitoring**

## 🎨 Caratteristiche dell'Interfaccia

### Design Moderno
- **Gradiente di sfondo** blu-viola
- **Cards trasparenti** con effetto glass
- **Animazioni fluide** sui pulsanti
- **Icone FontAwesome** per migliore UX

### Tabella Avanzata
- **Header fisso** durante lo scroll
- **Altezza limitata** con scroll verticale
- **Colori dell'efficienza**:
  - 🟢 Verde: ≥ 80% (Alta efficienza)
  - 🟡 Giallo: 50-79% (Media efficienza)  
  - 🔴 Rosso: < 50% (Bassa efficienza)

### Responsive Design
- **Mobile-friendly**
- **Layout adattivo** per tutti i dispositivi
- **Font ottimizzati** per la leggibilità

## 🔧 Endpoint API

### POST `/analyze`
**Parametri:**
- `username`: Nome del curator
- `days_back`: Giorni da analizzare

**Risposta:**
```json
{
  "success": true,
  "data": [...],
  "statistics": {...},
  "username": "tasuboyz",
  "days_back": 7
}
```

### GET `/export_csv`
**Parametri query:**
- `username`: Nome del curator
- `days_back`: Giorni da analizzare

**Risposta:** File CSV scaricabile

### GET `/health`
**Risposta:**
```json
{
  "status": "healthy",
  "working_nodes": 3,
  "nodes": ["https://api.moecki.online", ...]
}
```

## 📝 Formula dell'Efficienza

```
Efficienza % = (Reward SP Effettivo / Valore Voto Stimato) × 100
```

- **> 100%**: Il curator ha ottenuto più di quanto stimato
- **= 100%**: Perfetta corrispondenza tra stima e realtà
- **< 100%**: Il curator ha ottenuto meno di quanto stimato

## 🚀 Avvio Rapido

1. **Installa le dipendenze:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Avvia l'applicazione:**
   ```bash
   python app.py
   ```

3. **Apri il browser:**
   ```
   http://localhost:5000
   ```

4. **Analizza un curator:**
   - Inserisci username (es. "tasuboyz")
   - Seleziona giorni (es. 7)
   - Clicca "Analizza Curator"

5. **Esporta i dati:**
   - Clicca "Esporta CSV" dopo l'analisi
   - Il file verrà scaricato automaticamente

## 🎯 Casi d'Uso

### 📊 Analisi Performance
- Valutare l'efficienza di curation
- Identificare pattern temporali
- Confrontare diversi curatori

### 📈 Ottimizzazione Strategia
- Analizzare timing dei voti
- Valutare ROI della curation
- Identificare autori profittevoli

### 🔬 Ricerca e Sviluppo
- Esportare dati per ML/AI
- Analisi statistiche avanzate
- Sviluppo algoritmi predittivi

## ⚠️ Note Tecniche

- **Timeout API**: 5 secondi per connessione
- **Failover automatico** tra nodi Steem
- **Cache locale** dei risultati durante la sessione
- **Gestione errori** completa con messaggi user-friendly
