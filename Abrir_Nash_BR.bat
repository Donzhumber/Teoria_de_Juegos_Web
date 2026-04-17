@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "PORT=8788"
set "URL=http://127.0.0.1:%PORT%/"

set "CHROME="
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" set "CHROME=%LocalAppData%\Google\Chrome\Application\chrome.exe"

set "PY=py -3"
where py >nul 2>&1 || set "PY=python"

%PY% -c "import streamlit" >nul 2>&1
if errorlevel 1 (
  echo Instale dependencias: %PY% -m pip install -r requirements.txt
  pause
  exit /b 1
)

echo Iniciando Streamlit en %URL% ...
start "Streamlit NashBR" /MIN %PY% -m streamlit run app.py --server.headless true --server.port %PORT% --browser.gatherUsageStats false

set /a N=0
:wait
curl -s -o nul -w "%%{http_code}" "%URL%" 2>nul | findstr "200" >nul
if not errorlevel 1 goto openurl
set /a N+=1
if %N% GEQ 90 goto fail
timeout /t 1 /nobreak >nul
goto wait

:openurl
if defined CHROME (
  start "" "%CHROME%" "%URL%"
) else (
  start "" "%URL%"
)
echo Listo: se abrio Google Chrome si estaba instalado; si no, el navegador predeterminado.
echo Cierre la ventana minimizada "Streamlit NashBR" para detener el servidor.
pause
exit /b 0

:fail
echo No se pudo contactar el servidor. Compruebe que el puerto %PORT% este libre.
pause
exit /b 1
