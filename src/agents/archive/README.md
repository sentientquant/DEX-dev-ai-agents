# Archived RBI Agents

This directory contains archived RBI (Research-Based Inference) agent variants that are no longer in active development.

## Archive Date
2025-11-10

## Reason for Archive
Focus development on single, multi-provider RBI agent (`rbi_agent_pp_multi.py`)

## Archived Agents

| Agent File | Description | Reason for Archive |
|-----------|-------------|-------------------|
| `rbi_agent_pp.py` | Single-provider RBI agent | Superseded by multi-provider version |
| `rbi_agent_v2.py` | Version 2 RBI agent | Similar pattern, consolidated functionality |
| `rbi_agent_v2_simple.py` | Simplified v2 variant | Similar pattern, consolidated functionality |
| `rbi_agent_v3.py` | Version 3 RBI agent | Similar pattern, consolidated functionality |

## Active RBI Agents

| Agent File | Purpose |
|-----------|---------|
| `rbi_agent.py` | Original/base RBI agent |
| `rbi_agent_pp_multi.py` | **PRIMARY AGENT** - Multi-provider RBI with parallel processing |

## Notes

- All archived agents had similar patterns and shared the same bugs
- They used same libraries (housecoin_agent.py and swarm_agent.py also had same bugs)
- Focus is now exclusively on `rbi_agent_pp_multi.py` for all RBI functionality
- These files are preserved for reference but should not be modified or used in production

## Recovery

If you need to restore any of these agents:
```bash
git mv src/agents/archive/[agent_name].py src/agents/[agent_name].py
```
