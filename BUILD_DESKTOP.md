# WORKOUT Generator desktop packages

This document describes how to build the current test packages for Windows and macOS.

## Goal

Produce desktop packages that start the local WORKOUT Generator server and open the browser automatically:

- Windows: `WORKOUTGenerator.exe`
- macOS Intel: `WORKOUT Generator.app`
- macOS Apple Silicon: `WORKOUT Generator.app`

The user does not need Python, Flask, Git, PowerShell, or npm to run the packaged application.

## Automated build with GitHub Actions

The repository workflow is:

`.github/workflows/release-windows.yml`

Despite the historical filename, it now builds all desktop targets.

The workflow runs:

1. the Python test suite;
2. the Windows PyInstaller build;
3. the macOS Intel PyInstaller build;
4. the macOS Apple Silicon PyInstaller build;
5. artifact upload.

For a version tag (`v*`) the generated files are also attached to the GitHub Release.

### Manual test build

From GitHub:

1. open **Actions**;
2. select **Build Desktop Packages**;
3. choose **Run workflow**;
4. select the branch to test;
5. wait for all jobs to finish;
6. download the three artifacts from the workflow run.

No Mac is required locally: the macOS packages are built by GitHub-hosted macOS runners.

## Windows package

PyInstaller uses:

`garmin_workout_generator.spec`

Expected output:

`dist/WORKOUTGenerator.exe`

The executable starts the local server on:

`http://127.0.0.1:8780`

and opens the default browser.

## macOS packages

PyInstaller uses:

`workout_generator_macos.spec`

The workflow builds separately for Intel and Apple Silicon, then archives the app as ZIP.

Expected artifacts:

- `WORKOUT-Generator-macOS-Intel.zip`
- `WORKOUT-Generator-macOS-Apple-Silicon.zip`

Inside each archive:

`WORKOUT Generator.app`

These first test builds are not Apple-notarized. Gatekeeper may therefore show a warning on another Mac. Signing and notarization are a later release-hardening step.

## Important: WORKOUT Link publisher authentication

The desktop package must **not** contain the shared `WOL_PUBLISHER_KEY`.

The current development app can read that key from an environment variable or from the local development file `wol/.dev.vars`. That mechanism is appropriate for the current private/test creator workflow, but it is not suitable for a public downloadable application because embedding a shared publisher secret in the executable would expose it.

Therefore:

- building and testing the desktop application is safe now;
- JSON generation and the local builder can be tested normally;
- public distribution with WORKOUT Link publishing requires a creator-authentication mechanism that does not ship a shared secret inside the app.

Do not add `WOL_PUBLISHER_KEY` to GitHub Actions build secrets for embedding into the generated binary.

## Release status

Desktop packaging is currently **EXPERIMENTAL** until the generated Windows and macOS packages are downloaded and tested on their respective operating systems.
