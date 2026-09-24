# WorkOutLink — PoC 1

Primo componente eseguibile di WorkOutLink (WOL).

Stato corrente:

```text
[IMPLEMENTED]  D1 schema
[VALIDATED REMOTE] POST /api/publish/plan
[VALIDATED REMOTE] GET /p/<public_id>
[IMPLEMENTED]  GET /privacy
[PREPARED]     OAuth Intervals.icu (app approval pending)
[PREPARED]     bulk delivery (not yet end-to-end validated)
[TODO]         Garmin end-to-end via link pubblico
[TODO]         Suunto end-to-end
```

## Setup locale

```powershell
cd wol
npm install
npx wrangler login
npx wrangler d1 create workoutlink-db
```

Copia il `database_id` restituito da Wrangler in `wrangler.jsonc`, sostituendo:

```text
REPLACE_AFTER_D1_CREATE
```

Poi:

```powershell
npm run db:local
```

Crea `wol/.dev.vars`:

```text
WOL_PUBLISHER_KEY=<chiave-casuale-lunga>
```

`.dev.vars` è ignorato da Git.

Avvio:

```powershell
npm run dev
```

Per produzione, il secret va configurato con Wrangler:

```powershell
npx wrangler secret put WOL_PUBLISHER_KEY
```

## Pubblicazione di prova

```powershell
$headers = @{
  Authorization = "Bearer <WOL_PUBLISHER_KEY>"
  "Content-Type" = "application/json"
}

$body = @{
  title = "Settimana PoC"
  description = "Primo piano pubblico WOL"
  items = @(
    @{ day_offset = 1; workout = @{ name = "6x1000" } },
    @{ day_offset = 3; workout = @{ name = "Facile + allunghi" } },
    @{ day_offset = 5; workout = @{ name = "Lungo" } }
  )
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:8787/api/publish/plan" `
  -Headers $headers `
  -Body $body
```

La risposta contiene `public_id` e `url`. Apri l'URL nel browser.

## Stato del PoC

In questa fase implementiamo solo:

```text
publisher -> WOL -> link pubblico
```

Il codice per OAuth Intervals.icu e bulk delivery è ora predisposto ma resta **gated**: non viene attivato finché l'app OAuth WorkOutLink non è approvata e i secret non sono configurati.

Endpoint predisposti:

```text
GET  /oauth/intervals/start
GET  /oauth/intervals/callback
POST /api/deliver/plan
```

Scope richiesto dal PoC:

```text
CALENDAR:WRITE
```

Il token OAuth viene mantenuto solo lato server e cifrato prima della memorizzazione in D1.

Secret da configurare dopo l'approvazione:

```text
INTERVALS_CLIENT_ID
INTERVALS_CLIENT_SECRET
SESSION_SECRET
```

Non inserire questi valori nel repository.


## Milestone validata

Il 2026-09-22 è stato validato il primo flusso pubblico remoto:

```text
publisher key
-> POST /api/publish/plan
-> Cloudflare Worker
-> D1 remoto
-> public_id
-> URL workers.dev
-> pagina pubblica visualizzata correttamente nel browser
```

Stato: `VALIDATED REMOTE` per il tratto publishing + public page.

OAuth Intervals.icu e delivery verso Garmin/Suunto restano da implementare e validare.


## OAuth application status

La richiesta OAuth **WorkOutLink** è stata inviata a Intervals.icu il 2026-09-23 ed è attualmente in stato `Pending`.

Redirect URI registrata:

```text
https://workoutlink.paolo-ricciotti.workers.dev/oauth/intervals/callback
```

Categoria richiesta: sincronizzazione allenamenti.

Webhook: nessuno per il PoC 1.

Il flusso OAuth reale non può essere promosso a `VALIDATED` finché l'app non viene approvata e provata con un atleta reale.
