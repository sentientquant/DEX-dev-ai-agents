@echo off
REM Type checking script for Windows
REM Run this to check type safety of migrated modules

echo ========================================
echo TYPE CHECKING MIGRATED MODULES
echo ========================================
echo.

echo [1/5] Checking domain models...
python -m mypy trading_modes\models\domain.py --config-file=mypy.ini
if %ERRORLEVEL% NEQ 0 (
    echo [FAIL] Domain models have type errors
) else (
    echo [PASS] Domain models OK
)
echo.

echo [2/5] Checking result type...
python -m mypy trading_modes\models\result.py --config-file=mypy.ini
if %ERRORLEVEL% NEQ 0 (
    echo [FAIL] Result type has type errors
) else (
    echo [PASS] Result type OK
)
echo.

echo [3/5] Checking technical indicators...
python -m mypy trading_modes\indicators\technical.py --config-file=mypy.ini
if %ERRORLEVEL% NEQ 0 (
    echo [FAIL] Technical indicators have type errors
) else (
    echo [PASS] Technical indicators OK
)
echo.

echo [4/5] Checking signal verification agent...
python -m mypy trading_modes\core\signal_verification_agent.py --config-file=mypy.ini
if %ERRORLEVEL% NEQ 0 (
    echo [FAIL] Signal verification agent has type errors
) else (
    echo [PASS] Signal verification agent OK
)
echo.

echo [5/5] Checking typed database...
python -m mypy risk_management\trading_database_typed.py --config-file=mypy.ini
if %ERRORLEVEL% NEQ 0 (
    echo [FAIL] Typed database has type errors
) else (
    echo [PASS] Typed database OK
)
echo.

echo ========================================
echo TYPE CHECK COMPLETE
echo ========================================
echo.
echo To generate HTML report, run:
echo   python -m mypy trading_modes\models trading_modes\indicators --html-report mypy_report
echo.

pause
