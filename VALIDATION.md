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

### Repeat block

Validati:

- `numberOfIterations`;
- child step ordinati;
- lavoro + recupero;
- recupero a distanza;
- lavoro a distanza;
- lavoro a tempo;
- più `RepeatGroupDTO` nello stesso workout;
- target FC differenti tra lavoro e recupero.

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
- `stepId: null`;
- Tasto LAP senza target;
- Tasto LAP con Zona FC.

## VALIDATED_REFERENCE

### Passo

La struttura:

```text
pace.zone
```

è presente nei riferimenti Garmin osservati.

La generazione dinamica da un intervallo espresso in min/km non è ancora validata dal progetto corrente.

### Lap button

Storicamente era classificato `VALIDATED_REFERENCE`.

Dal 2026-09-19 la struttura base `lap.button` è stata promossa a `VALIDATED` per le combinazioni effettivamente importate:

- nessun target;
- Zona FC.

Altre combinazioni LAP restano da validare singolarmente.

## EXPERIMENTAL

Restano sperimentali finché non vengono verificati con import reale:

- conversione dinamica passo min/km -> valori Garmin;
- eventuali target cadenza;
- combinazioni LAP non ancora testate, ad esempio LAP + FC personalizzata;
- strutture Garmin non presenti nei riferimenti o non ancora importate dal generatore.

## Regola di validazione

Una nuova struttura non diventa `VALIDATED` perché:

- sembra coerente;
- è presente nella documentazione;
- è osservata in un riferimento;
- passa i test unitari.

Diventa `VALIDATED` solo dopo che un JSON generato dal progetto viene importato con successo in Garmin Connect e il comportamento risultante è coerente con l'intento dell'allenamento.
