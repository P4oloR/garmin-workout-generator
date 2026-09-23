# WORKOUT Product Family — Brand System

Status: **ACTIVE**

The project uses a shared product-family identity built around the master brand **WORKOUT**.

## Product names

Public-facing names:

- **WORKOUT Generator**
- **WORKOUT Link**

Internal technical shorthand may continue to use `WOG` and `WOL`, but these abbreviations are not the primary public brand.

## Product roles

### WORKOUT Generator

Purpose: create, build and publish structured workouts and weekly plans.

Tagline:

```text
CREATE • BUILD • PUBLISH
```

Primary symbol: three ascending rounded bars.

Visual accent: mint / sage green.

### WORKOUT Link

Purpose: share, schedule and deliver published plans to athletes.

Tagline:

```text
SHARE • SCHEDULE • DELIVER
```

Brand claim:

```text
One plan. One link. Ready to train.
```

Primary symbol: interlocking chain links.

Visual accent: sun yellow.

## Shared visual language

Both products use the same master wordmark:

```text
WORKOUT
```

The product name appears as the secondary line:

```text
Generator
Link
```

Shared characteristics:

- bold geometric sans-serif master wordmark;
- rounded product-name typography;
- light neutral application background;
- teal hero surfaces;
- white cards;
- rounded corners;
- restrained shadows;
- product-specific accent color;
- compact uppercase product tagline.

## Color palette

Reference palette:

| Token | Role | Hex |
| --- | --- | --- |
| Deep Teal | primary brand | `#00695C` |
| Teal | primary UI | `#00796B` |
| Sage | Generator secondary | `#5EB48C` |
| Mint | Generator accent | `#B7E5CE` |
| Sun | Link accent | `#FBC02D` |
| Orange | support / interval accent | `#FF5722` |
| Fog | neutral background | `#F6F8F7` |
| Ink | dark text | `#173C35` |

## Naming rules

Preferred:

```text
WORKOUT Generator
WORKOUT Link
```

Avoid as public-facing product names:

```text
WOG
WOL
WorkOutGenerator
WorkOutLink
Garmin Workout Generator
```

Technical filenames, environment variables and historical code may retain previous naming when changing them would create unnecessary compatibility work.

## Current implementation

The shared brand system is implemented in:

```text
templates/index.html
static/style.css
wol/src/index.js
```

The Generator and Link products intentionally share the same visual foundation while retaining different symbols and accent colors.
