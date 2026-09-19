# Garmin Standalone Workout Generator

Local standalone web application for building structured running workouts
and generating Garmin Connect compatible JSON files.

## Status

Early development / MVP.

## Principles

- Independent from FAA2
- No Garmin personal IDs hardcoded
- Internal workout model separated from Garmin JSON
- Garmin structures classified as VALIDATED, VALIDATED_REFERENCE or EXPERIMENTAL
- New Garmin structures require real import testing before being considered stable