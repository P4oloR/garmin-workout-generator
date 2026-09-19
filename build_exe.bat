@echo off
setlocal

cd /d "%~dp0"

echo.
echo ==========================================
echo  Garmin Workout Generator - Windows build
echo ==========================================
echo.

echo [1/5] Installazione dipendenze applicazione...
python -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo.
echo [2/5] Installazione dipendenze build...
python -m pip install -r requirements-build.txt
if errorlevel 1 goto :error

echo.
echo [3/5] Esecuzione test...
python -m unittest discover -s tests -v
if errorlevel 1 goto :error

echo.
echo [4/5] Pulizia build precedente...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo [5/5] Creazione EXE...
python -m PyInstaller --clean --noconfirm garmin_workout_generator.spec
if errorlevel 1 goto :error

echo.
echo ==========================================
echo BUILD COMPLETATA
echo.
echo File:
echo   dist\GarminWorkoutGenerator.exe
echo ==========================================
echo.
pause
exit /b 0

:error
echo.
echo ==========================================
echo BUILD FALLITA
echo Controllare gli errori mostrati sopra.
echo ==========================================
echo.
pause
exit /b 1
