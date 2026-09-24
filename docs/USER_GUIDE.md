# WorkOut Generator
## Manuale utente passo-passo

Questo manuale spiega come:

1. installare quello che serve sul PC;
2. scaricare WorkOut Generator da GitHub;
3. avviare il programma;
4. creare un allenamento;
5. generare il file `.json`;
6. importarlo in Garmin Connect.

Non è necessario saper programmare.

---

# 1. Cosa serve

Prima di iniziare servono:

- un PC Windows;
- una connessione Internet;
- un account Garmin Connect;
- Python installato sul PC;
- Git installato sul PC;
- Google Chrome o un browser compatibile;
- l'estensione **Share Your Garmin Workout**.

WorkOut Generator funziona localmente sul PC e genera un file JSON Garmin.

---

# 2. Installare Python

Se Python è già installato, passa direttamente al capitolo successivo.

Apri il browser e vai su:

https://www.python.org/downloads/

Scarica Python per Windows e avvia il file appena scaricato.

## MOLTO IMPORTANTE

Nella prima schermata dell'installazione metti la spunta su:

```text
Add Python to PATH
```

Poi premi:

```text
Install Now
```

Quando l'installazione termina, chiudi la finestra.

## Controllo

Premi:

```text
Windows + R
```

scrivi:

```text
cmd
```

e premi Invio.

Nella finestra nera scrivi:

```bash
python --version
```

e premi Invio.

Se compare qualcosa simile a:

```text
Python 3.x.x
```

Python è installato correttamente.

---

# 3. Installare Git

Apri il browser e vai su:

https://git-scm.com/download/win

Scarica Git per Windows e avvia il programma di installazione.

Se non sai cosa scegliere nelle varie schermate, lascia le opzioni predefinite e continua premendo:

```text
Next
```

fino alla fine.

## Controllo

Apri il Prompt dei comandi e digita:

```bash
git --version
```

Se compare una versione di Git, l'installazione è riuscita.

---

# 4. Preparare la cartella del progetto

Apri il Prompt dei comandi.

Scrivi:

```bash
cd C:\
mkdir Progetti
cd C:\Progetti
```

Se la cartella `Progetti` esiste già, non è un problema.

---

# 5. Scaricare WorkOut Generator da GitHub

Nel Prompt dei comandi scrivi:

```bash
git clone URL_DEL_REPOSITORY
```

Esempio:

```bash
git clone https://github.com/NOME-UTENTE/garmin-workout-generator.git
```

> Sostituire `URL_DEL_REPOSITORY` con l'indirizzo reale del repository GitHub.

Poi entra nella cartella del progetto:

```bash
cd garmin-workout-generator
```

---

# 6. Installare le dipendenze

Questa operazione normalmente va fatta solo la prima volta.

Esegui:

```bash
python -m pip install -r requirements.txt
```

Se il comando termina senza errori, puoi procedere.

---

# 7. Avviare WorkOut Generator

Sempre dalla cartella del progetto esegui:

```bash
python app.py
```

Non chiudere la finestra del Prompt dei comandi.

---

# 8. Aprire il programma nel browser

Apri Chrome e vai a:

```text
http://127.0.0.1:8780
```

Dovrebbe comparire la schermata di WorkOut Generator.

Se la pagina non si apre, controlla che la finestra con:

```bash
python app.py
```

sia ancora aperta e non mostri errori.

---

# 9. Creare un allenamento

Dalla schermata principale configura l'allenamento.

A seconda delle funzioni disponibili puoi inserire:

- nome dell'allenamento;
- riscaldamento;
- distanza o durata;
- target di frequenza cardiaca;
- numero di ripetizioni;
- fase di lavoro;
- recupero;
- defaticamento.

Controlla l'anteprima prima di procedere.

---

# 10. Generare il file Garmin

Quando l'allenamento è pronto premi:

```text
GENERA JSON GARMIN
```

Il browser scaricherà un file con estensione:

```text
.json
```

Per esempio:

```text
3x1000.json
```

Normalmente il file viene salvato nella cartella `Download` di Windows.

Non modificare manualmente il file JSON.

---

# 11. Installare Share Your Garmin Workout

Per importare il file JSON utilizziamo l'estensione:

**Share Your Garmin Workout**

Repository:

https://github.com/fulippo/share-your-garmin-workout

Segui le istruzioni di installazione presenti nel repository dell'estensione.

Una volta installata, lasciala attiva nel browser.

---

# 12. Accedere a Garmin Connect

Apri Chrome e vai su:

https://connect.garmin.com/

Accedi normalmente con il tuo account Garmin.

WorkOut Generator **non richiede le tue credenziali Garmin**.

Il generatore crea solamente il file JSON sul tuo PC.

---

# 13. Importare l'allenamento

Una volta dentro Garmin Connect Web:

1. vai nella sezione degli allenamenti;
2. assicurati che l'estensione Share Your Garmin Workout sia attiva;
3. usa il comando di importazione aggiunto dall'estensione;
4. premi **Import Workout**;
5. seleziona il file `.json` creato con WorkOut Generator;
6. conferma l'importazione.

Se il file è accettato, il workout comparirà nel tuo account Garmin Connect.

---

# 14. Inviare il workout al dispositivo Garmin

Da questo momento il workout è presente in Garmin Connect.

Puoi quindi utilizzare le normali funzioni Garmin per inviarlo al dispositivo associato al tuo account.

Il flusso completo è:

```text
WorkOut Generator
        ↓
file JSON
        ↓
Share Your Garmin Workout
        ↓
Garmin Connect
        ↓
dispositivo Garmin
```

---

# 15. Come riaprire il programma nei giorni successivi

Apri il Prompt dei comandi ed esegui:

```bash
cd C:\Progetti\garmin-workout-generator
python app.py
```

Poi apri:

```text
http://127.0.0.1:8780
```

---

# 16. Come aggiornare WorkOut Generator

Apri il Prompt dei comandi e vai nella cartella del progetto:

```bash
cd C:\Progetti\garmin-workout-generator
```

Poi esegui:

```bash
git pull
```

Per sicurezza puoi aggiornare anche le dipendenze:

```bash
python -m pip install -r requirements.txt
```

Infine riavvia:

```bash
python app.py
```

---

# 17. Come chiudere WorkOut Generator

Torna alla finestra del Prompt dei comandi dove è in esecuzione:

```bash
python app.py
```

Premi:

```text
CTRL + C
```

Il server locale viene chiuso.

---

# Promemoria rapido

## La prima volta

```text
1. Installa Python
2. Installa Git
3. git clone ...
4. cd garmin-workout-generator
5. python -m pip install -r requirements.txt
6. python app.py
7. Apri http://127.0.0.1:8780
```

## Le volte successive

```text
1. Apri il Prompt dei comandi
2. cd C:\Progetti\garmin-workout-generator
3. python app.py
4. Apri http://127.0.0.1:8780
```

## Per creare un allenamento

```text
1. Crea il workout
2. Premi GENERA JSON GARMIN
3. Ottieni il file .json
4. Apri Garmin Connect Web
5. Usa Share Your Garmin Workout
6. Importa il file
7. Invia il workout al Garmin
```

---

# Se qualcosa non funziona

## `python` non viene riconosciuto

Probabilmente Python non è stato aggiunto al PATH.

Reinstalla Python assicurandoti di selezionare:

```text
Add Python to PATH
```

---

## `git` non viene riconosciuto

Chiudi il Prompt dei comandi, riaprilo e prova:

```bash
git --version
```

Se ancora non funziona, reinstalla Git.

---

## Il browser non apre `127.0.0.1:8780`

Controlla che sia ancora aperta la finestra dove hai eseguito:

```bash
python app.py
```

Se quella finestra è stata chiusa, il programma non è più in esecuzione.

---

## Garmin non importa il JSON

Non modificare manualmente il file.

Prova prima con un workout semplice e verifica che l'estensione Share Your Garmin Workout sia attiva.

---

# In una frase

**WorkOut Generator crea l'allenamento. Il percorso JSON Garmin tramite Share Your Garmin Workout resta disponibile come modalità legacy/fallback.**
