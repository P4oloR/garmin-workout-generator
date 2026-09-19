# Validation Status

This document records Garmin Connect import validations for the project.

## Validation policy

A Garmin structure is considered `VALIDATED` only after a JSON file produced by
this project has been imported successfully into Garmin Connect.

Structures observed in real Garmin exports but not yet generated and imported by
this project remain `VALIDATED_REFERENCE`.

Anything not yet confirmed by a successful import remains `EXPERIMENTAL`.

## 2026-09-19 — Easy + strides workout

Status: `VALIDATED`

A JSON produced by the project builder was imported successfully into Garmin
Connect with the following structure:

- Running workout root
- One workout segment
- Warmup: 7.5 km
- Custom heart-rate target: 125-138 bpm
- Repeat group: 6 iterations
- Interval: 20 seconds
- Recovery: 150 m
- Cooldown: 1 km
- Custom heart-rate target: 125-138 bpm

Validated Garmin structures in this test:

- `ExecutableStepDTO`
- `RepeatGroupDTO`
- distance end condition
- time end condition
- iterations end condition
- `no.target`
- `heart.rate.zone` with custom min/max bpm
- repeat group child steps
- `skipLastRestStep = false`
- `smartRepeat = false`
- preferred distance unit `kilometer`
- preferred distance unit `meter`

The generated file was accepted even though these derived root fields were left
as `null`:

- `estimatedDurationInSecs`
- `estimatedDistanceInMeters`
- `avgTrainingSpeed`
- `estimateType`
- `estimatedDistanceUnit`
- `workoutThumbnailUrl`

This confirms only that those fields were not required for this tested workout
combination. It does not prove that they are optional for every Garmin workout.

## Still experimental

The following remain unvalidated by project-generated import tests:

- automatic generation of Garmin `stepId` values
- dynamic pace targets
- cadence targets
- additional Garmin target types
- additional sport types
- multiple independent repeat blocks in one generated workout
