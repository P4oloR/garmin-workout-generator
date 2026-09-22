# Prerequisiti Intervals.icu

Questa sezione documenta i prerequisiti necessari per usare Intervals.icu come ponte tra Garmin Workout Generator e Garmin Connect.

## Account e connessioni

Prima di usare la sincronizzazione via Intervals.icu:

1. creare un account Intervals.icu;
2. generare una API key personale per i test locali;
3. collegare Garmin Connect da `Impostazioni -> Connessioni`;
4. abilitare `Carica allenamenti pianificati` per Garmin;
5. verificare che il dispositivo Garmin sia sincronizzato con Garmin Connect.

> Nota: per una futura versione multiutente non va usata una API key condivisa. L'integrazione dovrà passare a OAuth.

## Zone di frequenza cardiaca

Se un workout usa target basati su zone, ad esempio `Z2 HR` o `Z5 HR`, le zone di frequenza cardiaca devono essere configurate correttamente in Intervals.icu prima di creare o sincronizzare l'allenamento.

Intervals.icu usa le proprie zone HR dell'atleta per trasformare target come `Z2 HR` e `Z5 HR` in range BPM concreti. Garmin riceve quindi il range BPM risultante, non necessariamente la zona Garmin configurata sul dispositivo.

Esempio osservato durante i test:

```text
Z2 HR in Intervals.icu
        ↓
range BPM calcolato da Intervals.icu
        ↓
Garmin Connect
        ↓
Fenix: target mostrato come range BPM
```

Per questo motivo:

- prima di usare target a zona, controllare le zone HR in Intervals.icu;
- non è necessario che coincidano al singolo BPM con quelle Garmin, ma devono riflettere le zone che si vogliono realmente usare negli allenamenti;
- se le zone Intervals.icu non sono configurate correttamente, il workout può sincronizzarsi correttamente ma con target cardiaci diversi da quelli attesi.

## Ritmo soglia e zone passo

Se un workout usa target di passo (`Pace`), in Intervals.icu deve essere configurato il **Ritmo soglia** nelle impostazioni della corsa/passo prima di creare o sincronizzare l'allenamento.

Nei test end-to-end del progetto, con il Ritmo soglia non configurato il workout veniva sincronizzato, ma il target passo non veniva visualizzato correttamente sul Garmin. Dopo aver impostato il Ritmo soglia in Intervals.icu, i target passo sono stati trasferiti e mostrati correttamente sull'orologio.

Il requisito è quindi riferito al flusso validato dal progetto:

```text
Ritmo soglia configurato in Intervals.icu
        ↓
zone passo disponibili in Intervals.icu
        ↓
target Pace del workout
        ↓
Garmin Connect
        ↓
Fenix: target mostrato come range passo
```

Per questo motivo:

- prima di usare target `Pace`, impostare il **Ritmo soglia** in Intervals.icu;
- verificare che Intervals.icu abbia generato correttamente le zone passo;
- per evitare conversioni indesiderate di un valore di passo singolo, il Garmin Workout Generator userà preferibilmente un **range passo esplicito**, ad esempio `4:28-4:32 Pace`;
- questo prerequisito è distinto dalla configurazione delle zone HR, che rimane necessaria per target come `Z1 HR`.

## Stato validazione

### VALIDATED

Testato end-to-end sia tramite PoC sia, per il golden test misto, tramite la GUI reale del Garmin Workout Generator:

- creazione workout via API Intervals.icu;
- sincronizzazione nel calendario Intervals.icu;
- upload verso Garmin Connect;
- sincronizzazione su Fenix;
- step a tempo;
- repeat block;
- tipi semantici `warmup`, `interval`, `recovery`, `cooldown`;
- target HR percentuale;
- target HR a zona, convertito da Intervals.icu in range BPM;
- target passo come range esplicito;
- combinazione nello stesso repeat block di target `Pace` e target a zona HR (`Z1 HR`);
- step a distanza per warmup, interval, recovery e cooldown;
- invio dalla GUI reale tramite API Intervals.icu;
- ricezione in Garmin Connect e verifica finale sull'orologio Garmin.

Golden test GUI validato il 2026-09-22: `3 km warmup -> 2x [1 km 4:28-4:32 Pace + 1 km Z1 HR] -> 2 km cooldown`.

### Da validare

- step `Press lap` / tasto LAP;
- ulteriori combinazioni di target e durata;
- flusso multiutente con OAuth.
