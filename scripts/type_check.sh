#!/bin/bash
# Type checking script for Linux/Mac
# Run this to check type safety of migrated modules

set -e

echo "========================================"
echo "TYPE CHECKING MIGRATED MODULES"
echo "========================================"
echo ""

echo "[1/5] Checking domain models..."
if python -m mypy trading_modes/models/domain.py --config-file=mypy.ini; then
    echo "[PASS] Domain models OK"
else
    echo "[FAIL] Domain models have type errors"
    exit 1
fi
echo ""

echo "[2/5] Checking result type..."
if python -m mypy trading_modes/models/result.py --config-file=mypy.ini; then
    echo "[PASS] Result type OK"
else
    echo "[FAIL] Result type has type errors"
    exit 1
fi
echo ""

echo "[3/5] Checking technical indicators..."
if python -m mypy trading_modes/indicators/technical.py --config-file=mypy.ini; then
    echo "[PASS] Technical indicators OK"
else
    echo "[FAIL] Technical indicators have type errors"
    exit 1
fi
echo ""

echo "[4/5] Checking signal verification agent..."
if python -m mypy trading_modes/core/signal_verification_agent.py --config-file=mypy.ini; then
    echo "[PASS] Signal verification agent OK"
else
    echo "[FAIL] Signal verification agent has type errors"
    exit 1
fi
echo ""

echo "[5/5] Checking typed database..."
if python -m mypy risk_management/trading_database_typed.py --config-file=mypy.ini; then
    echo "[PASS] Typed database OK"
else
    echo "[FAIL] Typed database has type errors"
    exit 1
fi
echo ""

echo "========================================"
echo "TYPE CHECK COMPLETE - ALL PASSED ✓"
echo "========================================"
echo ""
echo "To generate HTML report, run:"
echo "  python -m mypy trading_modes/models trading_modes/indicators --html-report mypy_report"
echo ""
