# WorkOutLink (WOL) — PoC 1 Technical Contract

## Stato

Specifiche tecniche del primo PoC **single publisher**.

Nessuna implementazione WOL è ancora inclusa in questo documento.

## Obiettivo del PoC 1

Validare il percorso minimo:

```text
WorkOut Generator
-> publish autenticato
-> WorkOutLink
-> link pubblico
-> atleta
-> OAuth Intervals.icu
-> bulk calendar
-> Garmin reale
```

In seguito lo stesso piano verrà validato su Suunto.

## Scope

Incluso:

- un solo publisher;
- pubblicazione di un piano settimanale;
- snapshot immutabile;
- URL pubblico;
- atleta senza account WOL;
- OAuth Intervals.icu;
- selezione settimana;
- delivery bulk;
- idempotenza;
- Garmin end-to-end;
- preparazione del percorso Suunto.

Escluso:

- multi-publisher;
- account creator;
- ruoli;
- dashboard creator completa;
- statistiche;
- Polar;
- billing;
- dominio custom obbligatorio.

---

## Endpoint minimi

### POST /api/publish/plan

Uso:

```text
WorkOut Generator -> WOL
```

Autenticazione:

```http
Authorization: Bearer <WOL_PUBLISHER_KEY>
```

Body concettuale:

```json
{
  "title": "Settimana 1 - 10K",
  "description": "Blocco soglia",
  "items": [
    {
      "day_offset": 1,
      "workout": {}
    },
    {
      "day_offset": 3,
      "workout": {}
    }
  ]
}
```

Il campo `workout` contiene lo snapshot serializzato del modello interno WOG.

Successo:

```json
{
  "public_id": "ABC123...",
  "url": "https://<wol-host>/p/ABC123..."
}
```

Errori minimi:

- `401` publisher key assente/non valida;
- `400` payload non valido;
- `500` errore storage.

### GET /p/:public_id

Pagina pubblica read-only del piano.

Deve mostrare:

- titolo;
- descrizione opzionale;
- giorni/workout;
- selezione del lunedì di inizio settimana;
- Garmin;
- Suunto;
- link alla configurazione iniziale/prerequisiti.

Non deve esporre:

- publisher key;
- token OAuth;
- JSON Garmin;
- dettagli interni D1;
- sintassi Intervals.icu.

### GET /oauth/intervals/start

Input logico:

```text
public_plan_id
week_start
destination
```

Responsabilità:

1. validare piano e data;
2. creare `state` casuale;
3. salvare il contesto OAuth lato server;
4. redirect a Intervals.icu con `CALENDAR:WRITE`.

### GET /oauth/intervals/callback

Responsabilità:

1. verificare `state`;
2. gestire `access_denied`;
3. scambiare `code` con access token;
4. associare token alla sessione anonima atleta;
5. ripristinare `public_plan_id`, `week_start`, `destination`;
6. riportare l'utente alla conferma delivery.

### POST /api/deliver/plan

Autenticazione atleta:

- session cookie WOL;
- token Intervals solo server-side.

Body:

```json
{
  "public_id": "ABC123...",
  "week_start": "2026-09-28",
  "destination": "garmin"
}
```

Responsabilità:

1. caricare snapshot;
2. calcolare date da `day_offset`;
3. trasformare ogni workout tramite adapter Intervals;
4. generare `external_id`;
5. chiamare bulk calendar API;
6. restituire esito.

Nota: `destination` è inizialmente metadata UX. Prima di promettere un routing selettivo Garmin/Suunto va verificato se Intervals consente di scegliere il singolo provider o se sincronizza verso tutte le integrazioni abilitate dell'atleta.

Questo punto deve restare esplicitamente **OPEN** finché non viene verificato.

### GET /privacy

Pagina privacy minima WOL.

Deve spiegare almeno:

- quali dati WOL memorizza;
- uso di OAuth Intervals.icu;
- nessuna password Garmin/Suunto raccolta;
- token trattati come segreti;
- possibilità di scollegare/rifare autorizzazione;
- finalità esclusiva di publishing/delivery.

---

## Schema D1 minimo

### public_plans

```sql
CREATE TABLE public_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    public_id TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'published',
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);
```

Indice:

```sql
CREATE UNIQUE INDEX idx_public_plans_public_id
ON public_plans(public_id);
```

### plan_items

```sql
CREATE TABLE plan_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    item_id TEXT NOT NULL,
    day_offset INTEGER NOT NULL,
    display_order INTEGER NOT NULL,
    workout_snapshot TEXT NOT NULL,
    FOREIGN KEY(plan_id) REFERENCES public_plans(id)
);
```

Vincoli applicativi:

```text
day_offset: 0..6
workout_snapshot: JSON serializzato
item_id: univoco nel piano
```

Indice consigliato:

```sql
CREATE INDEX idx_plan_items_plan_id
ON plan_items(plan_id);
```

### athlete_sessions

```sql
CREATE TABLE athlete_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL UNIQUE,
    intervals_athlete_id TEXT,
    access_token_encrypted TEXT,
    granted_scopes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

Il browser conserva solo `session_id` in cookie.

Il token OAuth non deve essere inviato al frontend.

### oauth_states

```sql
CREATE TABLE oauth_states (
    state TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    public_id TEXT NOT NULL,
    week_start TEXT NOT NULL,
    destination TEXT NOT NULL,
    created_at TEXT NOT NULL
);
```

I record devono essere temporanei e invalidati dopo uso o timeout.

---

## Segreti

Cloudflare secret/environment bindings:

```text
WOL_PUBLISHER_KEY
INTERVALS_CLIENT_ID
INTERVALS_CLIENT_SECRET
SESSION_SECRET / encryption secret
```

Mai nel repository.

Mai nel JavaScript client.

Mai nello snapshot pubblico.

---

## Cookie atleta

Nome proposto:

```text
wol_session
```

Proprietà richieste in produzione:

```text
HttpOnly
Secure
SameSite=Lax
Path=/
```

Il cookie contiene solo un identificatore casuale.

Non contiene access token.

---

## Public ID

Il `public_id` deve essere:

- casuale;
- ad alta entropia;
- non sequenziale;
- non derivato da ID database;
- sicuro da inserire in URL pubblico.

Il link pubblico è intenzionalmente condivisibile: chi possiede il link può leggere il piano.

---

## Publisher key

Il PoC 1 usa un solo segreto di publishing.

Regole:

- generata casualmente;
- configurata in WOG come variabile ambiente/config locale;
- configurata in WOL come secret;
- confrontata server-side;
- mai loggata;
- rotabile.

La publisher key non è un account e non è una soluzione multi-publisher.

---

## Delivery payload Intervals

Per ogni `PlanItem`:

```text
category = WORKOUT
type = Run
start_date_local = week_start + day_offset
name = workout.name
description = intervals_builder output
external_id = wol:<public_id>:<item_id>:<date>
```

Invio:

```text
POST /api/v1/athlete/0/events/bulk?upsert=true
Authorization: Bearer <athlete_access_token>
```

## Idempotenza

Stesso:

```text
public_id
+ item_id
+ date
```

=> stesso `external_id`.

Ripetere il delivery della stessa settimana non deve creare duplicati.

---

## Validazioni server-side

### Publish

Rifiutare:

- titolo vuoto;
- piano senza item;
- `day_offset` fuori 0..6;
- workout snapshot non valido;
- item duplicati;
- publisher key errata.

### Delivery

Rifiutare:

- `public_id` inesistente/disabilitato;
- `week_start` non valido;
- sessione atleta assente;
- token Intervals assente;
- piano vuoto;
- conversione Intervals non supportata.

Il PoC non deve alterare silenziosamente workout incompatibili.

---

## Prerequisiti atleta

La pagina pubblica deve avere una sezione breve "Configurazione iniziale".

Garmin:

```text
1. account Intervals.icu
2. Garmin collegato in Intervals.icu
3. Upload planned workouts attivo
4. zone HR configurate se il piano usa target HR
5. ritmo soglia / zone passo configurati se usa target Pace
```

Suunto:

```text
1. account Intervals.icu
2. Suunto collegato in Intervals.icu
3. Upload planned workouts attivo
4. zone/target configurati secondo i requisiti del workout
5. compatibilità da validare sul dispositivo
```

---

## Flusso UX PoC 1

### Publisher

```text
WOG
-> crea più workout
-> compone settimana
-> anteprima
-> PUBBLICA SU WOL
-> riceve URL
-> copia/condivide link
```

### Atleta

```text
apre /p/<id>
-> vede settimana
-> sceglie lunedì di inizio
-> Garmin
-> collega Intervals.icu (solo se necessario)
-> conferma
-> AGGIUNGI SETTIMANA
-> conferma successo
```

---

## Stati di validazione

### Già VALIDATED

```text
WOG GUI
-> internal model
-> intervals_builder
-> Intervals API
-> Garmin Connect
-> Garmin reale
```

### Da validare nel PoC 1

```text
WOG
-> WOL publish
-> public URL
-> athlete OAuth
-> bulk delivery
-> Garmin reale
```

### Successivo

```text
stesso PublicPlan
-> WOL
-> Intervals
-> Suunto reale
```

---

## Open questions prima/durante implementazione

1. Verificare comportamento esatto del routing quando lo stesso atleta ha sia Garmin sia Suunto collegati a Intervals.icu.
2. Verificare lifecycle reale del bearer token OAuth.
3. Verificare formato esatto richiesto dal form di registrazione app OAuth al momento della creazione.
4. Definire hostname reale WOL prima di registrare la redirect URI definitiva.
5. Verificare se la cifratura applicativa del token in D1 è necessaria nel PoC o se usare storage separato/secret-backed più adatto.

Nessuno di questi punti richiede modifiche al modello interno `Workout`.

---

## Criterio di completamento

Il PoC 1 è completato solo quando:

```text
1. WOG pubblica una settimana autenticandosi con publisher key;
2. WOL restituisce un URL pubblico;
3. URL funziona da browser anonimo;
4. atleta autorizza Intervals via OAuth;
5. atleta sceglie la settimana;
6. WOL effettua il bulk insert;
7. un secondo invio non crea duplicati;
8. Intervals mostra correttamente tutti i workout;
9. Garmin Connect li riceve;
10. Garmin reale mostra struttura e target attesi.
```

Solo allora il percorso **WOL Public Delivery -> Garmin** può essere marcato `VALIDATED`.


---

## Milestone raggiunta: publishing remoto

Validato il 2026-09-22:

```text
single publisher
-> WOL publisher key
-> POST /api/publish/plan
-> Cloudflare Worker remoto
-> D1 remoto
-> public URL workers.dev
-> GET /p/<public_id>
-> pagina pubblica renderizzata correttamente
```

Questa milestone promuove il tratto **WOL publishing -> public page** a `VALIDATED REMOTE`.

Non promuove ancora a `VALIDATED` il percorso completo WOL Public Delivery, perché mancano:

- OAuth Intervals.icu;
- bulk delivery;
- sincronizzazione Garmin Connect;
- verifica su Garmin reale;
- successiva verifica Suunto.
