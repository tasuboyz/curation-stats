# Steem Curator Analyzer

Un potente strumento per analizzare l'attività di curation su Steem e preparare dati per modelli di machine learning.

## 🚀 Caratteristiche

- **Analisi completa dei curatori**: Estrae ricompense di curation e voti correlati
- **Dati temporali dettagliati**: Include minuto, ora e giorno della settimana dei voti
- **Metriche dei post**: Analizza lunghezza, categoria, tag, payout e engagement
- **Interfaccia web moderna**: Dashboard intuitiva con visualizzazione tabellare
- **Esportazione CSV**: Dati pronti per l'analisi in machine learning
- **Nodi multipli**: Utilizza diversi nodi Steem per alta disponibilità

## 🛠 Installazione

1. **Clona o scarica il progetto**
```bash
cd c:\Temp\test
```

2. **Installa le dipendenze**
```bash
pip install -r requirements.txt
```

## 📊 Utilizzo

### Interfaccia Web (Raccomandato)

1. **Avvia l'applicazione Flask**:
```bash
python app.py
```

2. **Apri il browser** all'indirizzo: `http://localhost:5000`

3. **Inserisci i parametri**:
   - Nome utente Steem (es. "steemitboard")
   - Numero di giorni da analizzare (default: 7)

4. **Visualizza i risultati** in una tabella dettagliata

5. **Esporta i dati** in formato CSV per ulteriori analisi

### Linea di Comando

```bash
python main.py
```

Segui le istruzioni a schermo per inserire:
- Nome del curatore
- Numero di giorni da analizzare

## 🌐 Nodi Steem Utilizzati

Il tool utilizza automaticamente questi nodi in ordine di priorità:
- `https://api.moecki.online`
- `https://api.steemit.com`
- `https://api.justyy.com`

## 📈 Dati Estratti

### Informazioni sui Voti
- **Timestamp completo**: Data, ora, minuto del voto
- **Peso del voto**: Percentuale di voto utilizzata
- **Giorno della settimana**: Per analisi dei pattern temporali

### Metriche dei Post
- **Titolo e categoria**
- **Lunghezza del contenuto**
- **Tag utilizzati**
- **Payout totale e pendente**
- **Numero di voti e commenti**
- **Reputazione dell'autore**

### Analisi Temporale
- **Tempo tra voto e reward**: In giorni e ore
- **Pattern di attività**: Orari e giorni preferiti per votare

## 🤖 Preparazione per Machine Learning

I dati esportati includono features numeriche e categoriche pronte per:
- **Classificazione**: Predire il successo di un post
- **Regressione**: Stimare il payout futuro
- **Clustering**: Identificare pattern di comportamento
- **Time Series**: Analizzare trend temporali

### Features Principali
- Variabili numeriche: 12+ features (ricompense, payout, lunghezza, ecc.)
- Variabili categoriche: 8+ features (autore, categoria, tag, ecc.)
- Variabili temporali: 5+ features (ora, minuto, giorno, ecc.)

## 📋 Esempio di Output

```
================================================================================
ANALISI CURATORE: ESEMPIO
Periodo: ultimi 7 giorni
================================================================================

STATISTICHE GENERALI:
- Numero totale rewards: 42
- Ricompensa totale: 1.234 STEEM
- Ricompensa media: 0.029 STEEM
- Peso voto medio: 85.2%
- Minuto medio di voto: 23.4

DATI PER MACHINE LEARNING:
- Features numeriche: 12
- Features categoriche: 8
```

## 🔧 Troubleshooting

### Errore di connessione ai nodi
- Il tool prova automaticamente diversi nodi
- Verifica la connessione internet
- Alcuni nodi potrebbero essere temporaneamente non disponibili

### Nessun dato trovato
- Verifica che l'username sia corretto
- L'utente potrebbe non aver attività di curation recenti
- Prova ad aumentare il numero di giorni da analizzare

### Errori di memoria
- Riduci il numero di giorni da analizzare
- Alcuni utenti molto attivi potrebbero generare molti dati

## 🎯 Casi d'Uso

1. **Analisi comportamentale**: Studia i pattern di voto dei curatori
2. **Ottimizzazione rewards**: Identifica le strategie più profittevoli
3. **Ricerca accademica**: Analizza l'economia delle blockchain social
4. **ML/AI Development**: Prepara dataset per modelli predittivi

## 📚 Dipendenze

- `beem==0.24.26`: Libreria Python per Steem
- `flask==2.3.3`: Framework web
- `pandas==2.0.3`: Manipolazione dati
- `tabulate==0.9.0`: Visualizzazione tabelle
- `python-dateutil==2.8.2`: Parsing date
- `requests==2.31.0`: HTTP client

## 🤝 Contributi

Il progetto è aperto a contributi! Aree di miglioramento:
- Supporto per altri blockchain social
- Visualizzazioni grafiche avanzate
- Algoritmi di machine learning integrati
- API REST per integrazione esterna

## 📄 Licenza

Progetto open source per uso educativo e di ricerca.

---

**Nota**: Questo strumento è per scopi di ricerca e analisi. Rispetta sempre i termini di servizio delle piattaforme analizzate.
