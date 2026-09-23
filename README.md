# WorkOut Generator

Generatore standalone di allenamenti strutturati, con modello interno indipendente dalla piattaforma.

Il progetto nasce come Garmin Workout Generator e mantiene il percorso Garmin JSON legacy già validato. La direzione corrente è però multipiattaforma: WorkOut Generator è il componente di authoring, mentre la pubblicazione e il delivery tramite link pubblico saranno affidati a **WorkOutLink (WOL)**. Il delivery Garmin via Intervals.icu è già validato end-to-end; Suunto è previsto tramite lo stesso bridge ma resta da validare sul dispositivo.

---

## Download rapido per Windows

Per usare il programma non è necessario installare Python o Git.

1. Apri la pagina **Releases** del progetto:
   https://github.com/P4oloR/garmin-workout-generator/releases
2. Scarica l'ultima versione di:
   `GarminWorkoutGenerator.exe`
3. Avvia il file con un doppio clic.
4. Si aprirà una piccola finestra launcher.
5. Il browser verrà aperto automaticamente su:
   `http://127.0.0.1:8780`

> Il programma gira solo sul PC locale. Il server Flask è accessibile esclusivamente tramite `127.0.0.1`.

---

## Prerequisito per importare il JSON in Garmin Connect

WorkOut Generator mantiene la possibilità di creare il file JSON Garmin dell'allenamento come percorso legacy/fallback.

Per importarlo in Garmin Connect Web è necessario usare l'estensione browser:

**Share Your Garmin Workout**

Repository:
https://github.com/fulippo/share-your-garmin-workout

L'estensione funziona da browser desktop e permette di importare/esportare workout Garmin in formato JSON.

### Flusso completo

```text
GarminWorkoutGenerator.exe
        ↓
creazione allenamento
        ↓
Genera JSON Garmin
        ↓
file .json
        ↓
Garmin Connect Web
        ↓
Share Your Garmin Workout
        ↓
Import workout
        ↓
Invia al dispositivo Garmin
```

---

## Utilizzo

### 1. Avvia il programma

Doppio clic su:

```text
GarminWorkoutGenerator.exe
```

Il launcher mostra lo stato:

```text
Attivo su http://127.0.0.1:8780
```

Il browser dovrebbe aprirsi automaticamente.

Se necessario, usa il pulsante:

```text
Apri Garmin Workout Generator
```

---

### 2. Crea l'allenamento

La GUI permette di aggiungere liberamente:

- step singoli;
- più blocchi di ripetute;
- riscaldamento;
- corsa;
- recupero;
- defaticamento;
- step "Altro".

Per ogni step è possibile scegliere il tipo di terminazione:

- distanza;
- tempo;
- tasto LAP.

---

## Target supportati

Sono supportati:

- nessun target;
- frequenza cardiaca personalizzata;
- zona FC;
- passo.

### Frequenza cardiaca personalizzata

Esempio:

```text
125–138 bpm
```

### Zona FC

Esempio:

```text
Z2
```

### Passo

Esempio:

```text
4:10–4:20 /km
```

Il programma converte internamente il passo nel formato richiesto da Garmin.

---

## Tasto LAP

Uno step può terminare manualmente tramite il pulsante LAP del dispositivo Garmin.

Esempio:

```text
Tipo: Tasto LAP
Target: Nessuno
```

oppure:

```text
Tipo: Tasto LAP
Target: Zona FC 2
```

Il target è indipendente dal tipo di terminazione ed è quindi opzionale.

---

## Blocchi di ripetute

È possibile creare più blocchi di ripetute nello stesso allenamento.

Esempio:

```text
2.5 km riscaldamento · Z1

4 ×
  100 m lavoro
  150 m recupero

500 m corsa · Z1

3 ×
  2000 m · 4:10–4:20/km
  500 m recupero

1 km defaticamento
```

---

## Generazione del JSON

Quando l'allenamento è valido, premi:

```text
GENERA JSON GARMIN
```

Il browser scaricherà un file `.json`.

Il file può quindi essere importato in Garmin Connect Web tramite **Share Your Garmin Workout**.

---

## Chiudere il programma

Per terminare correttamente WorkOut Generator usa il pulsante:

```text
Chiudi
```

presente nella finestra launcher.

Questo arresta anche il server locale.

---

# Installazione da sorgente

Questa sezione è destinata a chi vuole eseguire o modificare il progetto da Python.

## Requisiti

- Windows
- Python 3.14
- Git

## Clona il repository

Apri PowerShell:

```powershell
cd C:\Progetti
git clone https://github.com/P4oloR/garmin-workout-generator.git
cd garmin-workout-generator
```

## Installa le dipendenze

```powershell
python -m pip install -r requirements.txt
```

## Avvia l'app

```powershell
python app.py
```

Poi apri:

```text
http://127.0.0.1:8780
```

---

# Pubblicazione su WorkOutLink

WorkOut Generator include ora una workspace **Settimana WOL**.

Flusso previsto:

```text
crea workout
-> scegli giorno
-> AGGIUNGI ALLA SETTIMANA
-> modifica/crea il workout successivo
-> aggiungi gli altri giorni
-> PUBBLICA SU WOL
-> ricevi link pubblico
```

Per il PoC single-publisher, WOG usa la publisher key locale. In sviluppo la legge dalla variabile ambiente `WOL_PUBLISHER_KEY` oppure, se presente, da:

```text
wol/.dev.vars
```

Il backend pubblico predefinito è:

```text
https://workoutlink.paolo-ricciotti.workers.dev
```

Questa integrazione non modifica `models.py` e mantiene separati i percorsi legacy Garmin e Intervals.icu.

---

# Test

Per eseguire tutti i test automatici:

```powershell
python -m unittest discover -s tests -v
```

Il progetto include test per:

- modello interno;
- Garmin JSON builder;
- blocchi multipli;
- zone FC;
- tasto LAP;
- target passo;
- regressione rispetto ai riferimenti Garmin validati.

---

# Creazione dell'EXE

Per creare localmente l'eseguibile Windows:

```powershell
.\build_exe.bat
```

La build:

1. installa le dipendenze;
2. installa PyInstaller;
3. esegue i test;
4. pulisce le vecchie build;
5. genera l'eseguibile.

Output:

```text
dist\GarminWorkoutGenerator.exe
```

Per maggiori dettagli consulta:

```text
BUILD_WINDOWS.md
```

---

# Release Windows automatica

Il repository usa GitHub Actions.

Quando viene pubblicato un tag, ad esempio:

```powershell
git tag v1.0.1
git push origin v1.0.1
```

GitHub:

1. avvia una macchina Windows;
2. installa le dipendenze;
3. esegue i test;
4. crea `GarminWorkoutGenerator.exe`;
5. crea la GitHub Release;
6. allega l'EXE alla Release.

Le versioni pubblicate sono disponibili qui:

https://github.com/P4oloR/garmin-workout-generator/releases

---

# Struttura principale del progetto

```text
garmin-workout-generator/
├─ app.py
├─ models.py
├─ garmin_builder.py
├─ launcher.py
├─ garmin_workout_generator.spec
├─ requirements.txt
├─ requirements-build.txt
├─ build_exe.bat
├─ BUILD_WINDOWS.md
├─ VALIDATION.md
├─ templates/
│  └─ index.html
├─ static/
│  └─ style.css
├─ tests/
└─ .github/
   └─ workflows/
      └─ release-windows.yml
```

---

# Validazione

Il progetto distingue tra funzionalità e percorsi:

- `VALIDATED`
- `VALIDATED_REFERENCE`
- `EXPERIMENTAL`

Una struttura viene considerata `VALIDATED` solo dopo che un JSON generato dal progetto viene importato con successo in Garmin Connect e produce il comportamento atteso.

Consulta:

```text
VALIDATION.md
```

per il dettaglio delle strutture validate.

---

# Documentazione WorkOutLink

- [Architettura WOL](docs/WOL_ARCHITECTURE.md)
- [Contratto piano pubblico WOL](docs/WOL_PUBLIC_PLAN.md)
- [OAuth Intervals.icu per WOL](docs/WOL_OAUTH.md)
- [PoC 1 tecnico WOL](docs/WOL_POC1_TECHNICAL.md)
- [WorkOutLink PoC eseguibile](wol/README.md)

---

# Architettura attuale

```text
WorkOut Generator (WOG)
        ↓
authoring / modello interno
        ↓
├─ garmin_builder.py → JSON Garmin legacy
└─ intervals_builder.py → Intervals.icu

WorkOutLink (WOL) [PoC 1 in implementazione]
        ↓
link pubblico / publishing / delivery
        ↓
Intervals.icu
   ├─ Garmin
   └─ Suunto (da validare)
```

Il repository non viene rinominato in questa fase e i nomi tecnici legacy (eseguibile, spec e builder Garmin) restano invariati finché non sarà pianificata una migrazione controllata.

---

# Note

- Il progetto non contiene ID Garmin personali hardcoded.
- I `stepId` possono essere generati come `null` nelle combinazioni già validate.
- La GUI e il generatore funzionano localmente.
- Il percorso JSON Garmin resta disponibile come legacy/fallback; il percorso Intervals.icu è già validato end-to-end verso Garmin.
- Un EXE non firmato digitalmente può mostrare un avviso Windows SmartScreen.

---

# Licenza

Consulta il file:

```text
LICENSE
```


## WOG -> WOL remote publishing

Validato end-to-end il 2026-09-23:

```text
WorkOut Generator GUI locale
-> composizione settimana
-> PUBBLICA SU WOL
-> endpoint /publish-to-wol
-> WorkOutLink Worker remoto
-> D1 remoto
-> URL pubblico
-> pagina WOL corretta
```

Stato: **VALIDATED** per il tratto authoring/publishing WOG -> WOL remoto.

La validazione ha incluso una settimana con più workout assegnati a giorni differenti e la corretta visualizzazione del piano pubblico.
