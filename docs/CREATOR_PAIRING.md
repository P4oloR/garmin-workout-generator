# WORKOUT Link creator pairing (beta)

## Goal

Allow multiple WORKOUT Generator installations/creators to publish independently without embedding the shared `WOL_PUBLISHER_KEY` in the desktop application.

This is a beta device-pairing system, not yet a full user-account system.

## Flow

1. WORKOUT Generator shows **COLLEGA WORKOUT LINK**.
2. The creator enters a display name.
3. Generator requests a short-lived pairing from WORKOUT Link.
4. The browser opens the WORKOUT Link confirmation page.
5. The creator approves that Generator.
6. WORKOUT Link creates a random creator token.
7. Generator retrieves the token once and stores it in the operating-system credential store using Python `keyring`.
8. Future publications use that creator token as a Bearer token.
9. WORKOUT Link stores only the SHA-256 hash of the long-lived creator token.
10. Disconnecting a Generator revokes that creator token server-side and removes it locally.

## Storage

WORKOUT Link D1 tables:

- `creators`
- `creator_pairings`
- `public_plans.creator_id`

Pairing tokens are short lived (15 minutes). The long-lived creator token is only returned once to the paired Generator.

On desktop:

- Windows: keyring uses the Windows credential store.
- macOS: keyring uses the macOS Keychain.

## Legacy fallback

`WOL_PUBLISHER_KEY` remains accepted as a development/admin fallback while the beta pairing flow is validated. It must not be embedded in public desktop packages.

## Existing remote D1 database

Apply:

```powershell
cd wol
npx wrangler d1 execute workoutlink-db --remote --file=./migrations/0002_creator_pairing.sql
```

Then deploy:

```powershell
npm run deploy
```

## Status

Creator pairing is **EXPERIMENTAL** until validated end-to-end with a packaged WORKOUT Generator build.
