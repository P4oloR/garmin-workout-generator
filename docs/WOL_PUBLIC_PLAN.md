# WorkOutLink (WOL) — Public Plan Contract

## Obiettivo

Definire il contratto minimo del piano pubblico WOL senza modificare il modello interno `Workout`.

L'MVP usa la **settimana** come unità principale di pubblicazione.

## Principio

Il workout resta l'unità atomica.

Il piano settimanale è un contenitore di snapshot di workout associati a giorni relativi.

```text
WeekPlan
├─ Tuesday   Workout A
├─ Thursday  Workout B
├─ Saturday  Workout C
└─ Sunday    Workout D
```

Non servono date assolute nel piano pubblico.

## Perché usare giorni relativi

Lo stesso link deve poter essere usato da atleti diversi in settimane diverse.

Esempio:

```text
Piano:
Martedì  Ripetute
Giovedì  Facile
Sabato   Lungo

Atleta A:
settimana dal 28/09/2026

Atleta B:
settimana dal 05/10/2026
```

Il contenuto del piano rimane identico.

## Contratto concettuale

### PublicPlan

```text
public_id
title
description?
created_at
status = published | disabled
version
items[]
```

### PlanItem

```text
item_id
day_offset
display_order
workout_snapshot
```

Per una settimana con lunedì come giorno 0:

```text
0 = lunedì
1 = martedì
2 = mercoledì
3 = giovedì
4 = venerdì
5 = sabato
6 = domenica
```

## Snapshot immutabile

Un piano pubblicato non deve cambiare silenziosamente se l'autore modifica successivamente il workout nell'editor.

MVP:

```text
Publish
-> crea snapshot immutabile
-> genera public_id
```

Se l'autore cambia il piano, pubblica una nuova versione/link.

Una futura gestione versioni può riutilizzare lo stesso concetto, ma non è richiesta nell'MVP.

## UX autore

Flusso desiderato:

```text
CREA SETTIMANA

Lun  —
Mar  6x1000
Mer  —
Gio  Facile + allunghi
Ven  —
Sab  Lungo
Dom  Recovery

[ANTEPRIMA]
[PUBBLICA SETTIMANA]
```

L'autore non deve pubblicare manualmente un link per ogni workout.

## UX atleta

Pagina pubblica anonima:

```text
SETTIMANA DI ALLENAMENTO

Martedì
6x1000

Giovedì
Facile + allunghi

Sabato
Lungo

Domenica
Recovery

Inizia la settimana da:
[ Lunedì 28 settembre 2026 ]

[ GARMIN ]   [ SUUNTO ]

Polar
Prossimamente
```

L'atleta non deve vedere:

- JSON;
- API key;
- sintassi Intervals.icu;
- `external_id`;
- builder;
- dettagli OAuth tecnici.

## Calcolo date

L'atleta sceglie solo il lunedì di inizio settimana.

WOL calcola:

```text
event_date = week_start + day_offset
```

Il piano può quindi essere caricato con una sola operazione bulk nel calendario Intervals.icu.

## Delivery bulk

Intervals.icu documenta:

```text
POST /api/v1/athlete/0/events/bulk?upsert=true
```

con un array di eventi.

Per ciascun item WOL genera:

```text
category = WORKOUT
start_date_local = data calcolata
type = Run
name = nome workout
description = output intervals_builder.py
external_id = id stabile WOL
```

Riferimento:

https://forum.intervals.icu/t/uploading-planned-workouts-to-intervals-icu/63624

## Duplicati

Il delivery deve essere idempotente.

Esempio di `external_id`:

```text
wol:<public_plan_id>:<item_id>:<YYYY-MM-DD>
```

Se l'utente preme due volte "Aggiungi settimana", WOL usa lo stesso `external_id` e `upsert=true`.

## Singolo workout

WOL può supportare anche:

```text
/w/<public_id>
```

per un singolo workout.

Ma il flusso primario dell'MVP è:

```text
/p/<public_id>
```

per una settimana.

## Compatibilità

La compatibilità è responsabilità del delivery layer, non del modello Workout.

Esempio:

```text
Garmin via Intervals:
VALIDATED per il golden workout attuale

Suunto via Intervals:
EXPERIMENTAL finché non validato su dispositivo
```

Un piano pubblico può esistere anche se non tutte le destinazioni sono validate.

La UI deve mostrare chiaramente eventuali limitazioni.

## Costo zero

Il piano pubblico non deve richiedere:

- pagamento WOL;
- account WOL atleta;
- API key personale;
- abbonamento obbligatorio imposto dal nostro servizio.

Intervals.icu e il provider dispositivo possono avere proprie condizioni; WOL deve evitare funzionalità che rendano obbligatorio un piano a pagamento per il flusso base.

## Success criteria MVP

Il Public Plan PoC è completato quando:

```text
1. autore pubblica una settimana;
2. ottiene un URL pubblico;
3. URL è apribile senza login;
4. atleta sceglie data di inizio;
5. atleta autorizza Intervals.icu;
6. WOL inserisce tutti i workout nel calendario Intervals;
7. doppio click non duplica gli eventi;
8. Garmin riceve la settimana;
9. stesso piano viene poi validato su Suunto.
```
