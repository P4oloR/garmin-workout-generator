# Creare GarminWorkoutGenerator.exe

Questa procedura crea una versione Windows portable di Garmin Workout Generator.

L'utente finale non deve installare Python, Flask o Git.

## Prerequisiti per chi crea la build

Sul PC di sviluppo:

- Windows
- Python 3.14
- repository `garmin-workout-generator`

## Build locale

Aprire PowerShell nella cartella del progetto e lanciare:

```powershell
.\build_exe.bat
```

Lo script:

1. installa le dipendenze dell'app;
2. installa PyInstaller;
3. esegue tutti i test;
4. pulisce le vecchie cartelle `build` e `dist`;
5. crea l'eseguibile.

Se la build termina correttamente:

```text
dist\GarminWorkoutGenerator.exe
```

## Test dell'EXE

Fare doppio clic su:

```text
dist\GarminWorkoutGenerator.exe
```

Dovrebbe apparire una piccola finestra launcher e aprirsi automaticamente:

```text
http://127.0.0.1:8780
```

Verificare:

- apertura della GUI;
- creazione workout;
- generazione JSON;
- import del JSON in Garmin Connect;
- chiusura dell'app tramite il pulsante `Chiudi`.

## GitHub Release automatica

Il repository contiene:

```text
.github/workflows/release-windows.yml
```

Quando viene pubblicato un tag, ad esempio:

```powershell
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions:

1. crea un ambiente Windows;
2. installa le dipendenze;
3. esegue i test;
4. costruisce `GarminWorkoutGenerator.exe`;
5. crea/aggiorna la GitHub Release associata al tag;
6. allega l'EXE alla Release.

## Build manuale tramite GitHub Actions

La workflow può anche essere avviata manualmente dalla scheda `Actions`.

In questo caso viene prodotto un artifact scaricabile, ma non viene creata una Release perché non esiste un tag.

## File da non versionare

Le cartelle/file generati localmente devono restare fuori dal repository:

```text
build/
dist/
*.exe
```

## Nota Windows SmartScreen

Una prima versione non firmata digitalmente può mostrare un avviso di Windows SmartScreen.
Questo non dipende da Flask o da Garmin; è comune per nuovi eseguibili non firmati.

In futuro è possibile aggiungere una firma digitale del codice.
