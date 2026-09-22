# WorkOutLink (WOL) — Architecture

## Stato

Documento di specifica. Nessun codice WOL è implementato in questa fase.

## Scopo

WorkOutLink (WOL) è il componente pubblico di publishing e delivery che si affianca a **WorkOut Generator (WOG)**.

Responsabilità:

```text
WorkOut Generator (WOG)
= authoring
= creazione workout
= modello interno
= builder/exporter

WorkOutLink (WOL)
= publishing
= link pubblico
= OAuth Intervals.icu
= delivery verso Garmin / Suunto
```

Polar è fuori scope fino allo studio di un possibile percorso TrainingPeaks.

## Vincoli di progetto

1. Esperienza utente il più semplice possibile.
2. L'autore deve poter preparare e pubblicare più workout senza perdersi.
3. Una settimana è l'unità principale dell'MVP.
4. Adesione al progetto a costo zero per autore e atleta.
5. Nessun account WOL obbligatorio per l'atleta nell'MVP.
6. Nessuna password Garmin o Suunto deve transitare in WOL.
7. Il modello interno `Workout` non va modificato senza una necessità concreta.
8. `garmin_builder.py` rimane disponibile come percorso legacy/fallback Garmin.

## Architettura logica

```text
┌──────────────────────┐
│ WorkOut Generator    │
│ GUI + models.py      │
└──────────┬───────────┘
           │
        Publish
           │
           ▼
┌──────────────────────┐
│ WorkOutLink          │
│ Public snapshot      │
│ Public URL           │
└──────────┬───────────┘
           │
      Athlete opens
           │
           ▼
┌──────────────────────┐
│ WOL Delivery         │
│ OAuth Intervals.icu  │
└──────────┬───────────┘
           │
   intervals_builder.py
           │
           ▼
┌──────────────────────┐
│ Intervals.icu        │
│ Athlete calendar     │
└───────┬────────┬─────┘
        │        │
        ▼        ▼
     Garmin    Suunto
   VALIDATED   TO VALIDATE

Legacy:
models.py -> garmin_builder.py -> Garmin JSON
```

## Publishing

Il publishing crea uno snapshot pubblico e immutabile del workout o del piano.

Lo snapshot:

- non contiene API key;
- non contiene token OAuth;
- non contiene password Garmin/Suunto;
- non dipende dal dispositivo dell'atleta;
- non contiene JSON Garmin come formato canonico.

Il link pubblico appartiene a WOL, non a Intervals.icu.

Forme previste:

```text
/w/<public_id>   singolo workout
/p/<public_id>   piano/settimana
```

Per l'MVP il piano settimanale è il flusso principale.

## Delivery

WOL usa Intervals.icu come bridge.

Per modificare il calendario dell'atleta l'app OAuth deve richiedere almeno:

```text
CALENDAR:WRITE
```

La guida Intervals.icu per planned workouts documenta:

```text
POST /api/v1/athlete/0/events/bulk?upsert=true
```

con array di eventi, supporto a `external_id` e workout definiti tramite `description` nella sintassi nativa Intervals.icu.

Riferimenti:

- OAuth: https://forum.intervals.icu/t/intervals-icu-oauth-support/2759
- Planned workout API: https://forum.intervals.icu/t/uploading-planned-workouts-to-intervals-icu/63624
- API cookbook: https://forum.intervals.icu/t/intervals-icu-api-integration-cookbook/80090

## Idempotenza

Ogni evento inviato da WOL deve avere un `external_id` stabile.

Forma concettuale:

```text
wol:<plan_public_id>:<item_id>:<date>
```

Con `upsert=true`, un doppio click dell'utente non deve creare duplicati.

La guida Intervals.icu specifica che `external_id` viene confrontato con eventi creati dalla stessa applicazione.

## Hosting MVP

Candidato attuale:

```text
Cloudflare Workers
+ Cloudflare D1
```

Motivazione:

- piano Workers Free disponibile;
- D1 disponibile anche sul piano Free;
- sufficiente per un MVP/PoC a basso volume;
- frontend, API e storage possono stare nello stesso ecosistema.

Limiti correnti da monitorare:

- Workers Free: 100.000 richieste/giorno;
- D1 Free: 5 milioni righe lette/giorno;
- D1 Free: 100.000 righe scritte/giorno;
- D1 Free: 5 GB storage totale.

Riferimenti:

- https://developers.cloudflare.com/workers/platform/limits/
- https://developers.cloudflare.com/d1/platform/pricing/
- https://developers.cloudflare.com/d1/platform/limits/

Il requisito "costo zero" è un vincolo di prodotto: se una dipendenza essenziale richiede in futuro un piano a pagamento, il flusso deve essere rivalutato.

## Dati minimi

WOL deve salvare solo quanto necessario.

### PublicPlan

```text
public_id
title
description (opzionale)
created_at
status
version
```

### PlanItem

```text
plan_id
item_id
day_offset
display_order
workout_snapshot
```

### IntervalsConnection

```text
session/user reference
intervals_athlete_id
access_token
granted_scopes
created_at
```

Non assumere l'esistenza di refresh token o di una specifica scadenza token finché non è documentata/verificata nel flusso reale.

## Stato delle piattaforme

### Garmin

`VALIDATED` per:

```text
WOG GUI
-> modello interno
-> intervals_builder.py
-> Intervals.icu
-> Garmin Connect
-> dispositivo Garmin reale
```

Il link pubblico WOL + OAuth non è ancora validato.

### Suunto

Intervals.icu supporta planned workouts verso Suunto, ma il percorso WOL -> Intervals -> Suunto deve essere validato su dispositivo reale prima di essere marcato `VALIDATED`.

### Polar

Fuori scope. Nessuna implementazione finché non viene studiato il percorso TrainingPeaks.

## Non-obiettivi MVP

Non implementare inizialmente:

- account WOL obbligatori per atleti;
- social/community;
- commenti;
- classifiche;
- statistiche avanzate;
- training plan lunghi mesi;
- integrazione Garmin API diretta;
- Polar;
- modifica del modello `Workout` solo per esigenze di publishing;
- rimozione del legacy Garmin JSON.
