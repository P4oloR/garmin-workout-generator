# VALIDATION

Questo documento registra esclusivamente le strutture e le combinazioni effettivamente osservate o importate con successo in Garmin Connect.

Data ultimo aggiornamento: 2026-09-19

## Stati

- `VALIDATED`: generato dal progetto e importato con successo in Garmin Connect.
- `VALIDATED_REFERENCE`: osservato in un JSON Garmin di riferimento, ma non ancora validato end-to-end dal generatore corrente.
- `EXPERIMENTAL`: struttura o conversione non ancora validata con import reale.

## VALIDATED

### Struttura workout running

Validati tramite import reale:

- root workout running;
- `workoutSegments`;
- `ExecutableStepDTO`;
- `RepeatGroupDTO`;
- più step singoli nello stesso workout;
- più blocchi di ripetute nello stesso workout;
- combinazioni miste `Step -> RepeatBlock -> Step -> RepeatBlock -> Step`.

### Step ID nullable

Per le strutture testate, Garmin Connect accetta:

```json
"stepId": null
```

Questo consente al generatore di non usare ID Garmin personali o hardcoded.

La validazione riguarda le combinazioni effettivamente testate e non costituisce una garanzia universale per ogni possibile struttura Garmin.

### Condizioni di fine step

#### Distanza

Validato:

```json
"endCondition": {
  "conditionTypeId": 3,
  "conditionTypeKey": "distance",
  "displayOrder": 3,
  "displayable": true
}
```

Unità preferite validate nelle strutture testate:

- metri;
- chilometri.

Il modello interno conserva la distanza in metri e mantiene separatamente l'unità preferita scelta dall'utente.

#### Tempo

Validato:

```json
"endCondition": {
  "conditionTypeId": 2,
  "conditionTypeKey": "time",
  "displayOrder": 2,
  "displayable": true
}
```

#### Tasto LAP

Validato end-to-end tramite GUI -> JSON -> Garmin Connect:

```json
"endCondition": {
  "conditionTypeId": 1,
  "conditionTypeKey": "lap.button",
  "displayOrder": 1,
  "displayable": true
}
```

Per la generazione corrente viene preservato il valore osservato nel riferimento Garmin:

```json
"endConditionValue": 1000.0
```

Non viene attribuito a questo valore un significato generale oltre alla struttura osservata e importata con successo.

Combinazioni LAP validate:

- Tasto LAP + nessun target;
- Tasto LAP + Zona FC.

### Target

#### Nessun target

Validato:

```json
"targetType": {
  "workoutTargetTypeId": 1,
  "workoutTargetTypeKey": "no.target",
  "displayOrder": 1
}
```

#### FC personalizzata

Validato:

```json
"targetType": {
  "workoutTargetTypeId": 4,
  "workoutTargetTypeKey": "heart.rate.zone",
  "displayOrder": 4
}
```

con:

- `targetValueOne` = FC minima;
- `targetValueTwo` = FC massima;
- `zoneNumber` = null.

#### Zona FC

Validato end-to-end anche dalla GUI dinamica multi-blocco:

```json
"targetType": {
  "workoutTargetTypeId": 4,
  "workoutTargetTypeKey": "heart.rate.zone",
  "displayOrder": 4
}
```

con:

```json
"targetValueOne": null,
"targetValueTwo": null,
"zoneNumber": 1
```

o altra zona valida scelta dall'atleta.

Le zone supportate dal modello corrente sono Z1-Z5.

#### Passo

Validato end-to-end tramite GUI -> JSON -> Garmin Connect.

La GUI accetta un intervallo espresso in `min/km`, ad esempio:

```text
4:10/km - 4:20/km
```

Il generatore converte i due limiti in velocità in metri al secondo:

```text
velocità_m_s = 1000 / secondi_per_km
```

Esempio:

```text
4:10/km = 250 s/km -> 4.0 m/s
4:20/km = 260 s/km -> 3.846153846... m/s
```

La struttura Garmin validata è:

```json
"targetType": {
  "workoutTargetTypeId": 6,
  "workoutTargetTypeKey": "pace.zone",
  "displayOrder": 6
}
```

con:

- `targetValueOne` = limite più veloce espresso in m/s;
- `targetValueTwo` = limite più lento espresso in m/s;
- `targetValueUnit` = null;
- `zoneNumber` = null.

La validazione attuale riguarda la combinazione realmente testata con un blocco di ripetute a distanza e target passo generato dalla GUI.

Non viene ancora estesa automaticamente a ogni possibile combinazione futura con:

- step LAP + passo;
- recupero + passo;
- step a tempo + passo;
- altre strutture non ancora importate.

### Repeat block

Validati:

- `numberOfIterations`;
- child step ordinati;
- lavoro + recupero;
- recupero a distanza;
- lavoro a distanza;
- lavoro a tempo;
- più `RepeatGroupDTO` nello stesso workout;
- target FC differenti tra lavoro e recupero;
- target passo sul lavoro nelle ripetute testate.

### GUI Flask

Validato il flusso completo:

```text
GUI Flask
-> modello interno
-> garmin_builder.py
-> JSON scaricato dal browser
-> import riuscito in Garmin Connect
```

Sono stati importati con successo workout generati dalla GUI contenenti:

- step singoli;
- blocchi di ripetute multipli;
- distanze in metri e chilometri;
- zone FC;
- FC personalizzata;
- `stepId: null`;
- Tasto LAP senza target;
- Tasto LAP con Zona FC;
- target Passo generato dinamicamente da valori in min/km.

## VALIDATED_REFERENCE

Le strutture presenti nei riferimenti Garmin ma non ancora promosse a `VALIDATED` per combinazioni specifiche restano qui finché non vengono testate end-to-end.

Esempi:

- eventuali combinazioni `lap.button` + target non ancora provate;
- combinazioni `pace.zone` diverse da quelle effettivamente importate dal generatore corrente.

## EXPERIMENTAL

Restano sperimentali finché non vengono verificati con import reale:

- eventuali target cadenza;
- LAP + FC personalizzata;
- LAP + Passo;
- recupero + Passo;
- step a tempo + Passo;
- strutture Garmin non presenti nei riferimenti o non ancora importate dal generatore.

## Regola di validazione

Una nuova struttura non diventa `VALIDATED` perché:

- sembra coerente;
- è presente nella documentazione;
- è osservata in un riferimento;
- passa i test unitari.

Diventa `VALIDATED` solo dopo che un JSON generato dal progetto viene importato con successo in Garmin Connect e il comportamento risultante è coerente con l'intento dell'allenamento.
