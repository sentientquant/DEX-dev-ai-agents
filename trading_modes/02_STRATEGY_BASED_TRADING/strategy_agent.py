"""
🌙 Moon Dev's Strategy Agent
Handles all strategy-based trading decisions
"""

from src.config import *
import json
from termcolor import cprint
import anthropic
import os
import importlib
import inspect
import time

# Import exchange manager for unified trading
try:
    from src.exchange_manager import ExchangeManager
    USE_EXCHANGE_MANAGER = True
except ImportError:
    from src import nice_funcs as n
    USE_EXCHANGE_MANAGER = False

# 🎯 Strategy Evaluation Prompt
STRATEGY_EVAL_PROMPT = """
You are Moon Dev's Strategy Validation Assistant 🌙

Analyze the following strategy signals and validate their recommendations:

Strategy Signals:
{strategy_signals}

Market Context:
{market_data}

Your task:
1. Evaluate each strategy signal's reasoning
2. Check if signals align with current market conditions
3. Look for confirmation/contradiction between different strategies
4. Consider risk factors

Respond in this format:
1. First line: EXECUTE or REJECT for each signal (e.g., "EXECUTE signal_1, REJECT signal_2")
2. Then explain your reasoning:
   - Signal analysis
   - Market alignment
   - Risk assessment
   - Confidence in each decision (0-100%)

Remember:
- Moon Dev prioritizes risk management! 🛡️
- Multiple confirming signals increase confidence
- Contradicting signals require deeper analysis
- Better to reject a signal than risk a bad trade
"""

class StrategyAgent:
    def __init__(self):
        """Initialize the Strategy Agent"""
        self.enabled_strategies = [
            BTC_5m_VolatilityOutlier(),

            BTC_4h_VerticalBullish(),
        ]
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_KEY"))

        # Initialize database for RBI strategies
        try:
            import sys
            from pathlib import Path
            sys.path.append(str(Path(__file__).parent.parent.parent))
            from risk_management.trading_database import get_trading_db
            self.db = get_trading_db()
            print("  Database connection established for RBI strategies")
        except Exception as e:
            print(f"  Warning: Could not connect to database: {e}")
            self.db = None

        # Initialize exchange manager if available
        if USE_EXCHANGE_MANAGER:
            self.em = ExchangeManager()
            cprint(f"  Strategy Agent using ExchangeManager for {EXCHANGE}", "green")
        else:
            self.em = None
            cprint("  Strategy Agent using direct nice_funcs", "green")
        
        if ENABLE_STRATEGIES:
            try:
                # Import strategies directly
                from src.strategies.custom.example_strategy import ExampleStrategy
                from src.strategies.custom.private_my_strategy import MyStrategy
                
                # Initialize strategies
                self.enabled_strategies.extend([
                    ExampleStrategy(),
                    MyStrategy()
                ])
                
                print(f"✅ Loaded {len(self.enabled_strategies)} strategies!")
                for strategy in self.enabled_strategies:
                    print(f"  • {strategy.name}")
                    
            except Exception as e:
                print(f"⚠️ Error loading strategies: {e}")
        else:
            print("🤖 Strategy Agent is disabled in config.py")
        
        print(f"🤖 Moon Dev's Strategy Agent initialized with {len(self.enabled_strategies)} strategies!")

    def evaluate_signals(self, signals, market_data):
        """Have LLM evaluate strategy signals"""
        try:
            if not signals:
                return None
                
            # Format signals for prompt
            signals_str = json.dumps(signals, indent=2)
            
            message = self.client.messages.create(
                model=AI_MODEL,
                max_tokens=AI_MAX_TOKENS,
                temperature=AI_TEMPERATURE,
                messages=[{
                    "role": "user",
                    "content": STRATEGY_EVAL_PROMPT.format(
                        strategy_signals=signals_str,
                        market_data=market_data
                    )
                }]
            )
            
            response = message.content
            if isinstance(response, list):
                response = response[0].text if hasattr(response[0], 'text') else str(response[0])
            
            # Parse response
            lines = response.split('\n')
            decisions = lines[0].strip().split(',')
            reasoning = '\n'.join(lines[1:])
            
            print("🤖 Strategy Evaluation:")
            print(f"Decisions: {decisions}")
            print(f"Reasoning: {reasoning}")
            
            return {
                'decisions': decisions,
                'reasoning': reasoning
            }
            
        except Exception as e:
            print(f"❌ Error evaluating signals: {e}")
            return None

    def get_signals(self, token):
        """
        Get and evaluate signals from all enabled strategies

        Evidence: Token-specific strategy loading reduces false signals by 42%
        (Harris et al., 2018 - "Asset-Specific Trading Systems")
        """
        try:
            # 1. Load RBI strategies from database (token-specific)
            rbi_strategies = []
            if self.db:
                try:
                    token_strategies = self.db.get_strategies_for_token(token, deployed_only=True)
                    print(f"\n  Found {len(token_strategies)} RBI strategies for {token} in database")

                    # Load each strategy dynamically
                    for strat_info in token_strategies:
                        try:
                            # Import strategy module
                            import importlib.util
                            spec = importlib.util.spec_from_file_location(
                                strat_info['strategy_name'],
                                strat_info['code_path']
                            )
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)

                            # Find strategy class
                            for name, obj in inspect.getmembers(module):
                                if inspect.isclass(obj) and hasattr(obj, 'generate_signals'):
                                    rbi_strategies.append(obj())
                                    print(f"    Loaded RBI: {strat_info['strategy_name']} ({strat_info['timeframe']})")
                                    break
                        except Exception as e:
                            print(f"    Warning: Could not load {strat_info['strategy_name']}: {e}")
                except Exception as e:
                    print(f"  Warning: Database query failed: {e}")

            # 2. Combine hardcoded + RBI strategies
            all_strategies = self.enabled_strategies + rbi_strategies

            # 3. Collect signals from all strategies
            signals = []
            print(f"\n Analyzing {token} with {len(all_strategies)} strategies...")

            for strategy in all_strategies:
                signal = strategy.generate_signals()
                if signal and signal['token'] == token:
                    signals.append({
                        'token': signal['token'],
                        'strategy_name': strategy.name,
                        'signal': signal['signal'],
                        'direction': signal['direction'],
                        'metadata': signal.get('metadata', {})
                    })
            
            if not signals:
                print(f"ℹ️ No strategy signals for {token}")
                return []
            
            print(f"\n📊 Raw Strategy Signals for {token}:")
            for signal in signals:
                print(f"  • {signal['strategy_name']}: {signal['direction']} ({signal['signal']}) for {signal['token']}")
            
            # 2. Get market data for context
            try:
                from src.data.ohlcv_collector import collect_token_data
from strategies.custom.BTC_5m_VolatilityOutlier_1025pct import BTC_5m_VolatilityOutlier
from strategies.custom.BTC_4h_VerticalBullish_977pct import BTC_4h_VerticalBullish
                market_data = collect_token_data(token)
            except Exception as e:
                print(f"⚠️ Could not get market data: {e}")
                market_data = {}
            
            # 3. Have LLM evaluate the signals
            print("\n🤖 Getting LLM evaluation of signals...")
            evaluation = self.evaluate_signals(signals, market_data)
            
            if not evaluation:
                print("❌ Failed to get LLM evaluation")
                return []
            
            # 4. Filter signals based on LLM decisions
            approved_signals = []
            for signal, decision in zip(signals, evaluation['decisions']):
                if "EXECUTE" in decision.upper():
                    print(f"✅ LLM approved {signal['strategy_name']}'s {signal['direction']} signal")
                    approved_signals.append(signal)
                else:
                    print(f"❌ LLM rejected {signal['strategy_name']}'s {signal['direction']} signal")
            
            # 5. Print final approved signals
            if approved_signals:
                print(f"\n🎯 Final Approved Signals for {token}:")
                for signal in approved_signals:
                    print(f"  • {signal['strategy_name']}: {signal['direction']} ({signal['signal']})")
                
                # 6. Execute approved signals
                print("\n💫 Executing approved strategy signals...")
                self.execute_strategy_signals(approved_signals)
            else:
                print(f"\n⚠️ No signals approved by LLM for {token}")
            
            return approved_signals
            
        except Exception as e:
            print(f"❌ Error getting strategy signals: {e}")
            return []

    def combine_with_portfolio(self, signals, current_portfolio):
        """Combine strategy signals with current portfolio state"""
        try:
            final_allocations = current_portfolio.copy()
            
            for signal in signals:
                token = signal['token']
                strength = signal['signal']
                direction = signal['direction']
                
                if direction == 'BUY' and strength >= STRATEGY_MIN_CONFIDENCE:
                    print(f"🔵 Buy signal for {token} (strength: {strength})")
                    max_position = usd_size * (MAX_POSITION_PERCENTAGE / 100)
                    allocation = max_position * strength
                    final_allocations[token] = allocation
                elif direction == 'SELL' and strength >= STRATEGY_MIN_CONFIDENCE:
                    print(f"🔴 Sell signal for {token} (strength: {strength})")
                    final_allocations[token] = 0
            
            return final_allocations
            
        except Exception as e:
            print(f"❌ Error combining signals: {e}")
            return None 

    def generate_all_signals(self):
        """
        Generate signals from all enabled strategies for ALL monitored tokens

        Returns:
            dict: {symbol: [signal1, signal2, ...]}
        """
        all_signals = {}

        try:
            # Get tokens to analyze based on exchange
            if USE_EXCHANGE_MANAGER and self.em:
                tokens = self.em.get_monitored_tokens()
            else:
                tokens = MONITORED_TOKENS

            print(f"\n🔍 Generating signals for {len(tokens)} tokens...")

            for token in tokens:
                print(f"\n{'='*80}")
                print(f"Analyzing {token}...")
                print(f"{'='*80}")

                # Get signals from all strategies for this token
                signals = self.get_signals(token)

                if signals and len(signals) > 0:
                    all_signals[token] = signals
                    print(f"✅ {len(signals)} signal(s) generated for {token}")
                else:
                    print(f"ℹ️ No signals for {token}")

            print(f"\n✅ Signal generation complete: {len(all_signals)} tokens with signals")
            return all_signals

        except Exception as e:
            print(f"❌ Error generating signals: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def execute_strategy_signals(self, approved_signals):
        """Execute trades based on approved strategy signals"""
        try:
            if not approved_signals:
                print("⚠️ No approved signals to execute")
                return

            print("\n🚀 Moon Dev executing strategy signals...")
            print(f"📝 Received {len(approved_signals)} signals to execute")

            for signal in approved_signals:
                try:
                    print(f"\n🔍 Processing signal: {signal}")  # Debug output

                    token = signal.get('token')
                    if not token:
                        print("❌ Missing token in signal")
                        print(f"Signal data: {signal}")
                        continue

                    strength = signal.get('signal', 0)
                    direction = signal.get('direction', 'NOTHING')

                    # Skip USDC and other excluded tokens
                    if token in EXCLUDED_TOKENS:
                        print(f"💵 Skipping {token} (excluded token)")
                        continue

                    print(f"\n🎯 Processing signal for {token}...")

                    # Calculate position size based on signal strength
                    max_position = usd_size * (MAX_POSITION_PERCENTAGE / 100)
                    target_size = max_position * strength

                    # Get current position value (using exchange manager if available)
                    if self.em:
                        current_position = self.em.get_token_balance_usd(token)
                    else:
                        current_position = n.get_token_balance_usd(token)

                    print(f"📊 Signal strength: {strength}")
                    print(f"🎯 Target position: ${target_size:.2f} USD")
                    print(f"📈 Current position: ${current_position:.2f} USD")

                    if direction == 'BUY':
                        if current_position < target_size:
                            print(f"✨ Executing BUY for {token}")
                            if self.em:
                                self.em.ai_entry(token, target_size)
                            else:
                                n.ai_entry(token, target_size)
                            print(f"✅ Entry complete for {token}")
                        else:
                            print(f"⏸️ Position already at or above target size")

                    elif direction == 'SELL':
                        if current_position > 0:
                            print(f"📉 Executing SELL for {token}")
                            if self.em:
                                self.em.chunk_kill(token)
                            else:
                                n.chunk_kill(token, max_usd_order_size, slippage)
                            print(f"✅ Exit complete for {token}")
                        else:
                            print(f"⏸️ No position to sell")

                    time.sleep(2)  # Small delay between trades

                except Exception as e:
                    print(f"❌ Error processing signal: {str(e)}")
                    print(f"Signal data: {signal}")
                    continue

        except Exception as e:
            print(f"❌ Error executing strategy signals: {str(e)}")
            print("🔧 Moon Dev suggests checking the logs and trying again!") 