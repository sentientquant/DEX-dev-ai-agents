#!/usr/bin/env python3
"""
Continuous Trading Loop

PERMANENT SOLUTION for automated trading cycle:
1. Check and update open positions
2. Generate new signals (if no duplicate positions)
3. Monitor performance
4. Decide when to go LIVE

NO PLACEHOLDERS - PRODUCTION GRADE
"""

import os
import sys
import io
import time
from pathlib import Path
from datetime import datetime

# Fix Windows encoding
if os.name == 'nt' and not isinstance(sys.stdout, io.TextIOWrapper):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except Exception:
        pass

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from run_paper_trading_with_risk import PaperTradingWithRisk
from monitor_paper_and_go_live import LiveTradingDecisionSystem


class ContinuousTradingLoop:
    """Continuous trading loop with risk management"""

    def __init__(self, loop_interval_minutes: int = 15):
        self.loop_interval_minutes = loop_interval_minutes
        self.paper_trading = PaperTradingWithRisk()
        self.monitor = LiveTradingDecisionSystem()
        self.iteration = 0

    def run_one_cycle(self):
        """Run one complete trading cycle"""

        self.iteration += 1

        print(f"\n{'='*80}")
        print(f"TRADING CYCLE #{self.iteration}")
        print(f"{'='*80}")
        print(f"Time: {datetime.now()}")
        print(f"{'='*80}\n")

        # Step 1: Check open positions
        print(f"[STEP 1/3] Checking open positions...")
        open_positions = self.monitor.check_open_positions()

        # Step 2: Generate new signals (will auto-block duplicates)
        print(f"\n[STEP 2/3] Generating new trading signals...")
        performance = self.paper_trading.run()

        # Step 3: Check if ready for LIVE
        print(f"\n[STEP 3/3] Checking LIVE deployment criteria...")
        ready, metrics = self.monitor.monitor_and_decide()

        if ready:
            print(f"\n🎉 CRITERIA MET! Ready for Binance LIVE deployment!")
            return True  # Signal to stop loop

        print(f"\n✅ Cycle #{self.iteration} complete")
        return False  # Continue loop

    def run_continuous(self):
        """Run continuous trading loop"""

        print(f"\n{'='*80}")
        print(f"CONTINUOUS TRADING LOOP STARTED")
        print(f"{'='*80}")
        print(f"Loop Interval: {self.loop_interval_minutes} minutes")
        print(f"Started: {datetime.now()}")
        print(f"{'='*80}\n")

        try:
            while True:
                # Run one cycle
                ready_for_live = self.run_one_cycle()

                if ready_for_live:
                    print(f"\n🎉 LIVE DEPLOYMENT CRITERIA MET!")
                    print(f"   Stopping automatic loop.")
                    print(f"   Run: python deploy_to_binance_live.py")
                    break

                # Wait for next cycle
                print(f"\n⏰ Waiting {self.loop_interval_minutes} minutes until next cycle...")
                print(f"   Next cycle at: {datetime.now() + timedelta(minutes=self.loop_interval_minutes)}")
                print(f"   Press Ctrl+C to stop\n")

                time.sleep(self.loop_interval_minutes * 60)

        except KeyboardInterrupt:
            print(f"\n\n⚠️  Loop stopped by user (Ctrl+C)")
            print(f"   Total cycles completed: {self.iteration}")
            print(f"   Ended: {datetime.now()}")

    def run_once(self):
        """Run just one cycle (for testing)"""

        print(f"\n{'='*80}")
        print(f"SINGLE TRADING CYCLE")
        print(f"{'='*80}\n")

        ready = self.run_one_cycle()

        print(f"\n{'='*80}")
        print(f"SINGLE CYCLE COMPLETE")
        print(f"{'='*80}")
        print(f"Ready for LIVE: {'YES ✅' if ready else 'NO ❌'}")

        return ready


if __name__ == "__main__":
    from datetime import timedelta

    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        # Run single cycle
        loop = ContinuousTradingLoop()
        loop.run_once()
    else:
        # Run continuous loop
        loop_interval = 15  # minutes (default)
        if len(sys.argv) > 1:
            try:
                loop_interval = int(sys.argv[1])
            except ValueError:
                print(f"Invalid interval, using default: {loop_interval} minutes")

        loop = ContinuousTradingLoop(loop_interval_minutes=loop_interval)
        loop.run_continuous()
