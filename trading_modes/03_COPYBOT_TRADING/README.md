# CopyBot Trading Mode

## Overview
Automatically copy trades from successful whale wallets. Follow the smart money without manual analysis.

## Key Characteristics
- **Speed**: 30-45 seconds per portfolio check
- **Cost**: Medium (~$5-10/day)
- **Control**: Zero (fully automated copying)
- **Success Rate**: Depends on whale selection
- **Default Status**: DISABLED (need whale wallets)

## How It Works

### Flow Diagram
```
Whale Wallet Addresses
         ↓
Monitor Blockchain/Exchange
         ↓
   Detect New Trade
         ↓
   Analyze Trade
(Size, Token, Entry Price)
         ↓
   Filter Trade
(Min size, known tokens, risk limits)
         ↓
   Copy Trade
(Same direction, scaled to your portfolio)
         ↓
   Monitor Position
         ↓
   Exit When Whale Exits
```

## Configuration

```python
TRADING_MODES = {
    'copybot': {
        'enabled': False,  # DISABLED until you add whale wallets
        'whale_wallets': [
            # Add successful trader wallet addresses here
            # '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',  # Example
        ],
        'copy_threshold_usd': 100,  # Only copy trades >$100
        'scale_factor': 0.01  # Copy 1% of whale's size
    }
}
```

## Adding Whale Wallets

### 1. Find Successful Wallets
Sources:
- **Nansen**: On-chain analytics ($150/month)
- **Etherscan/Solscan**: Free blockchain explorers
- **DeFi Llama**: Track top wallets
- **Twitter**: Follow successful traders
- **Discord**: Moon Dev's copybot channel

### 2. Verify Wallet Performance
Check:
- ✅ Consistent profits (>6 months)
- ✅ Reasonable trade sizes ($1k-$1M)
- ✅ Low leverage (< 10x)
- ✅ Diverse tokens (not pump & dump)
- ❌ Avoid: Random wallets, unverified traders

### 3. Add to Config
```python
'whale_wallets': [
    '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',  # Wallet 1
    'DRpbCBMxVnDK7maPM5tGv6MvB3v1sRMC7H3x6y5pump',  # Wallet 2 (Solana)
    '0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B',  # Wallet 3
]
```

## Running CopyBot

### Standalone
```bash
python trading_modes/03_COPYBOT_TRADING/copybot_agent.py
```

### With Main Orchestrator
```bash
# Enable in config.py first: 'enabled': True
python src/main.py
```

## Copy Logic

### Trade Size Scaling
Whale trades $10,000 → You trade $100 (1% scale factor)

```python
your_trade_size = whale_trade_size * scale_factor
```

**Configuration**:
```python
'scale_factor': 0.01  # 1% of whale's size
'scale_factor': 0.1   # 10% of whale's size (more aggressive)
```

### Position Matching
- **Whale buys BTC** → You buy BTC
- **Whale sells BTC** → You sell BTC
- **Whale holds** → You hold
- **Whale closes** → You close

### Entry Timing
- **Instant Copy**: Execute immediately (may get worse price)
- **Delayed Copy**: Wait 1-5 minutes (better price, may miss move)

**Default**: Instant copy (recommended)

### Exit Strategy
1. **Follow Whale Exit**: Close when whale closes (recommended)
2. **Independent Stops**: Use your own stop loss (riskier)
3. **Time-Based**: Close after X hours regardless

**Default**: Follow whale exit

## Risk Management

### Position Size Limits
Respect your portfolio limits:
- Max 30% per position
- Min $100 balance
- Max $50 loss per 12h

**CopyBot will NOT copy if**:
- Position would exceed 30% of portfolio
- Would breach risk limits
- Token not supported on your exchange

### Filtering Trades

**Minimum Trade Size**:
```python
'copy_threshold_usd': 100  # Only copy trades >$100
```

**Supported Tokens**:
Only copy tokens available on Binance (your exchange)

**Risk Score**:
CopyBot calculates risk score (0-100):
- High leverage = High risk
- Unknown token = High risk
- Large position = High risk

Skip trades with risk >70

## Advantages

### 1. No Analysis Required
- Whale does the research
- You just copy
- Save time

### 2. Proven Track Record
- Copy only successful wallets
- Historical performance visible

### 3. Diversification
- Follow multiple whales
- Different strategies
- Spread risk

## Disadvantages

### 1. Delayed Execution
You always execute AFTER the whale:
- Whale gets better price
- You get slippage
- May miss the move

### 2. No Context
You don't know WHY whale is trading:
- Might be exiting due to insider info
- Could be hedging other positions
- May be liquidating for cash needs

### 3. Whale Can Change
- Previously successful whale may blow up
- Strategy changes
- You're following blindly

## Whale Types

### 1. Momentum Traders
- Quick in/out
- High volume
- 5-20% gains
**Copy if**: You want active trading

### 2. Swing Traders
- Hold 1-7 days
- Medium volume
- 10-50% gains
**Copy if**: You want moderate activity

### 3. Long-Term Holders
- Hold weeks/months
- Low volume
- 50-500% gains
**Copy if**: You want patience-based returns

### 4. Arbitrage Traders
- Instant trades
- High frequency
- 0.1-2% gains per trade
**Copy if**: You have low-latency execution

## Monitoring CopyBot

### View Copied Trades
```bash
python trading_modes/03_COPYBOT_TRADING/copybot_agent.py --show-portfolio
```

Output:
```
==== COPYBOT PORTFOLIO ====
Following: 3 whale wallets
Open Positions: 5
Total Value: $450.25
24h P&L: +$12.30 (+2.8%)

Recent Copies:
1. BTC/USDT - Copied from Whale #1 - Entry: $105,000 - P&L: +$5.20
2. ETH/USDT - Copied from Whale #2 - Entry: $3,200 - P&L: -$2.10
3. SOL/USDT - Copied from Whale #3 - Entry: $180 - P&L: +$8.40
============================
```

## Cost Analysis

Per day (assuming 20 trades copied):
- **API calls**: ~$2-5 (blockchain monitoring)
- **Gas fees**: $0.50-2 per trade (Solana cheap, Ethereum expensive)
- **Slippage**: 0.1-0.5% per trade

**Total**: $5-10/day

## Integration with Risk Management

CopyBot respects ALL risk limits:
- Will NOT copy if would breach max loss
- Scales down position if too large
- Closes if portfolio hits risk limits
- AI override still applies

## When to Use CopyBot

### Good Use Cases
1. **No time for analysis**: Let whales do the work
2. **Learning phase**: See what successful traders do
3. **Diversification**: Add to your existing strategies
4. **Low confidence**: Don't trust your own analysis yet

### Bad Use Cases
1. **No whale wallets**: Need to find successful traders first
2. **High-frequency trading**: Execution delay kills profit
3. **Unique strategy**: If you have edge, don't copy others
4. **Illiquid tokens**: Slippage too high on small tokens

## Comparison to Other Modes

| Feature | CopyBot | AI Swarm | Strategy-Based | RBI Research |
|---------|---------|----------|----------------|--------------|
| Analysis | None (whale does it) | 6 AIs | Algorithm | Backtest |
| Speed | 30-45 sec | 60 sec | 5-10 sec | 6 min |
| Cost | $5-10/day | $33/day | $1-2/day | $2-5/day |
| Control | Zero | Low | High | High |
| Best For | Following | Complex decisions | Algorithmic | Creating |

## Performance Tracking

### Whale Leaderboard
CopyBot tracks each whale's performance:
```
Whale #1: +15.2% (30 trades, 18 wins)
Whale #2: +8.7% (50 trades, 32 wins)
Whale #3: -2.1% (10 trades, 4 wins) ⚠️ Consider removing
```

### Auto-Remove Underperformers
```python
'auto_remove_losing_whales': True,  # Remove if <-5% over 30 days
'min_trades_before_removal': 20  # Give whale 20 trades to prove
```

## Whale Discovery

### Moon Dev's Verified Whales (Future)
We're building a verified whale list:
- Tracked performance
- Risk scores
- Strategy descriptions
- Community ratings

**Status**: Coming soon to Discord

### DIY Whale Finding
1. Check Nansen "Smart Money" section
2. Look at top gainers on Etherscan
3. Follow successful Twitter traders
4. Ask in crypto Discord communities
5. Check leaderboards on exchanges

## Legal & Ethical Considerations

- **NOT financial advice**: You're responsible for trades
- **No guaranteed returns**: Past performance ≠ future results
- **Whale may front-run**: They see you copying, adjust strategy
- **Insider trading**: Whale may have info you don't
- **Pump & dump**: Whale may intentionally mislead

**Use at your own risk**

## Troubleshooting

### No Whale Trades Detected
- Verify wallet addresses correct
- Check blockchain connection
- Increase monitoring frequency

### Execution Too Slow
- Use Groq for fast decisions
- Reduce number of whales monitored
- Optimize API calls

### Too Many Bad Copies
- Increase `copy_threshold_usd`
- Add more filtering rules
- Remove underperforming whales

## Future Enhancements
- [ ] Social sentiment integration (copy when Twitter bullish)
- [ ] ML model to predict whale success
- [ ] Whale reputation system
- [ ] Copy only specific token types
- [ ] Exit before whale (predict exits)

## Best Practices
1. **Start with 1-2 whales**: Don't overextend
2. **Small scale factor**: Use 0.01 (1%) initially
3. **Monitor daily**: Check whale performance
4. **Paper trade first**: Test for 1 week
5. **Diversify whales**: Different strategies, tokens

## When to Disable
- **Whale underperforming**: <-5% over 30 days
- **Market regime change**: Whale's strategy not working
- **You found your edge**: Switch to Strategy-Based
- **Too expensive**: Gas fees eating profits

## Support
CopyBot is experimental. Whale selection is everything. Choose wisely.
