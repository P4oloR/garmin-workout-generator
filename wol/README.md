# WorkOutLink — PoC 1

Primo componente eseguibile di WorkOutLink (WOL).

Stato corrente:

```text
[IMPLEMENTED]  D1 schema
[VALIDATED REMOTE] POST /api/publish/plan
[VALIDATED REMOTE] GET /p/<public_id>
[IMPLEMENTED]  GET /privacy
[TODO]         OAuth Intervals.icu
[TODO]         bulk delivery
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

OAuth e delivery Intervals.icu arriveranno nel passaggio successivo.


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
