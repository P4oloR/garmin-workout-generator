# WorkOutLink (WOL) — OAuth Intervals.icu

## Obiettivo

Definire il flusso OAuth minimo necessario a WOL per inserire workout nel calendario Intervals.icu dell'atleta.

## Principio di sicurezza

WOL non deve chiedere o memorizzare:

- password Intervals.icu;
- password Garmin;
- password Suunto;
- API key personale Intervals dell'atleta.

Per una vera applicazione multiutente, Intervals.icu richiede OAuth.

Riferimento:

https://forum.intervals.icu/t/intervals-icu-oauth-support/2759

## Registrazione applicazione

Intervals.icu mette a disposizione il form:

https://intervals.icu/oauth/apply

L'app deve avere un proprietario Intervals.icu.

Dalla pagina di gestione dell'app sono disponibili:

- `client_id`;
- client secret;
- redirect URI;
- configurazione webhooks e altre opzioni.

Lo stato iniziale è `Pending`.

La documentazione Intervals.icu specifica che il flusso OAuth non può essere usato finché l'app non è approvata.

## Identità proposta

```text
App name:
WorkOutLink

Abbreviation:
WOL

Description:
WorkOutLink lets workout creators publish structured training plans
through a public link. Athletes can add the workouts to their own
Intervals.icu calendar and sync them to supported devices such as
Garmin and Suunto.
```

URL finali da fissare quando esiste l'hosting reale:

```text
Website:
https://<wol-host>/

Privacy:
https://<wol-host>/privacy

OAuth callback:
https://<wol-host>/oauth/intervals/callback
```

Non registrare redirect URI definitive inventate prima di avere un endpoint reale.

## Scope minimo

Per creare/modificare eventi calendario la guida Intervals.icu richiede:

```text
CALENDAR:WRITE
```

Riferimento:

https://forum.intervals.icu/t/uploading-planned-workouts-to-intervals-icu/63624

L'MVP non deve richiedere scope ACTIVITY o WELLNESS.

Eventuali scope aggiuntivi devono essere introdotti solo se emerge una necessità concreta.

## Authorization flow

### 1. Utente clicca Garmin o Suunto

WOL conserva in sessione:

```text
public_plan_id
week_start
destination
csrf_state
```

### 2. Redirect a Intervals.icu

Forma documentata:

```text
https://intervals.icu/oauth/authorize
  ?client_id=<client_id>
  &redirect_uri=<redirect_uri>
  &scope=CALENDAR:WRITE
  &state=<opaque_state>
```

Lo `state` deve essere imprevedibile e verificato al ritorno per proteggere il flusso.

### 3. Callback

Successo:

```text
/oauth/intervals/callback?code=...&state=...
```

Rifiuto:

```text
/oauth/intervals/callback?error=access_denied
```

### 4. Exchange code

Intervals.icu documenta:

```text
POST https://intervals.icu/api/oauth/token
```

con:

```text
client_id
client_secret
code
```

Il code deve essere scambiato rapidamente; la documentazione Intervals.icu indica una finestra di 2 minuti.

La risposta include almeno:

- bearer access token;
- scope concessi;
- athlete id;
- athlete name.

### 5. Delivery

Usare:

```text
Authorization: Bearer <access_token>
```

e per endpoint con athlete id:

```text
athlete/0
```

può riferirsi all'atleta associato al bearer token.

## Dati da conservare

Minimo:

```text
intervals_athlete_id
access_token
granted_scopes
created_at
```

Il token deve essere trattato come segreto.

Non salvare token nei PublicPlan o nei PlanItem.

## Token lifecycle

La documentazione usata per questa specifica non definisce un contratto completo e stabile su refresh token/scadenza.

Per questo motivo:

- non assumere refresh token;
- non inventare durata token;
- gestire risposte di autorizzazione fallita/revocata;
- se necessario, chiedere nuovamente OAuth all'utente.

Il comportamento reale va verificato durante il PoC OAuth.

## Sessione atleta

MVP senza account WOL:

```text
Public link
-> OAuth Intervals
-> sessione tecnica WOL
-> delivery
```

L'atleta non deve creare username/password WOL.

La sessione deve poter essere eliminata/scadere senza compromettere il piano pubblico.

## Error handling UX

### access_denied

Messaggio:

```text
Autorizzazione annullata.
Nessun allenamento è stato aggiunto.
```

### scope mancante

```text
WorkOutLink non ha il permesso necessario per aggiungere
allenamenti al calendario Intervals.icu.
Ricollega Intervals.icu e autorizza l'accesso al calendario.
```

### token non valido/revocato

```text
La connessione a Intervals.icu non è più valida.
Ricollega il tuo account.
```

### errore API Intervals

```text
Non è stato possibile aggiungere gli allenamenti.
Nessuna password o credenziale Garmin/Suunto è gestita da WorkOutLink.
Riprova più tardi.
```

## Garmin / Suunto connection

OAuth WOL autorizza WOL verso Intervals.icu.

Non autorizza direttamente Garmin o Suunto.

L'atleta deve avere nel proprio account Intervals.icu:

```text
Garmin:
Upload planned workouts attivo

oppure

Suunto:
Upload planned workouts attivo
```

WOL non deve chiedere credenziali del produttore.

## Costo zero

Il PoC OAuth deve essere progettato per funzionare con:

- account Intervals.icu gratuito;
- hosting WOL su free tier;
- nessun abbonamento WOL.

Prima del rilascio pubblico va comunque verificato che le condizioni API/OAuth Intervals.icu siano compatibili con l'uso previsto.

## PoC OAuth da validare

La milestone tecnica successiva, quando inizierà il codice WOL, è:

```text
1. pagina pubblica WOL;
2. click Garmin;
3. OAuth Intervals;
4. callback valida;
5. token bearer;
6. POST bulk calendar;
7. workout nel calendario Intervals dell'utente;
8. Garmin reale riceve workout;
9. ripetizione con Suunto.
```

Solo dopo il test su dispositivo il percorso viene promosso a `VALIDATED`.
