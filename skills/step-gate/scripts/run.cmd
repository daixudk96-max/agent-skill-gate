@echo off
setlocal
rem step-gate launcher for Windows: auto-select bin/<platform>/step-gate.exe
rem Agent-facing commands are status/next/complete/help only; everything else is
rem admin-only and requires an operator-provisioned token in the environment.
set "CMD=%1"
set "SUB=%2"
rem Agent whitelist: status/next/complete/help + chain status (two args).
rem NOTE: next is NOT read-only — it writes the step delivery receipt to
rem .step-gate/state.json (two-phase commit). It stays agent-facing.
set "READONLY="
if "%CMD%"=="status" set "READONLY=1"
if "%CMD%"=="next" set "READONLY=1"
if "%CMD%"=="complete" set "READONLY=1"
if "%CMD%"=="--help" set "READONLY=1"
if "%CMD%"=="-h" set "READONLY=1"
if "%CMD%"=="help" set "READONLY=1"
if "%CMD%"=="" set "READONLY=1"
if "%CMD%"=="chain" if "%SUB%"=="status" set "READONLY=1"
set "ADMIN_ONLY="
if not defined READONLY (
  if "%STEP_GATE_ADMIN_TOKEN%"=="" (
    echo [step-gate] command %CMD% is admin-only; contact the operator ^(see docs/ADMIN.md^) 1>&2
    exit /b 2
  )
  set "ADMIN_ONLY=--admin-only"
)
set "SKILL_DIR=%~dp0.."
set "START_DIR=%CD%"
set "BIN="
if exist "%SKILL_DIR%\bin\windows-x64\step-gate.exe" set "BIN=%SKILL_DIR%\bin\windows-x64\step-gate.exe"
if not defined BIN if exist "%SKILL_DIR%\bin\windows-arm64\step-gate.exe" set "BIN=%SKILL_DIR%\bin\windows-arm64\step-gate.exe"
if not defined BIN (
  echo [step-gate] no windows binary found under "%SKILL_DIR%\bin\" 1>&2
  exit /b 3
)
pushd "%SKILL_DIR%"
"%BIN%" %* --workdir "%START_DIR%" %ADMIN_ONLY%
set EC=%ERRORLEVEL%
popd
exit /b %EC%
