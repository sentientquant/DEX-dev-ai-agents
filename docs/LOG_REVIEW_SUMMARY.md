Windows PowerShell
Copyright (C) Microsoft Corporation. All rights reserved.

Install the latest PowerShell for new features and improvements! https://aka.ms/PSWindows

Loading personal and system profiles took 636ms.
PS C:\Users\oia89> cd C:\Users\oia89\OneDrive\Desktop\DEX-dev-ai-agents
PS C:\Users\oia89\OneDrive\Desktop\DEX-dev-ai-agents> .\venv\Scripts\Activate.ps1
(venv) PS C:\Users\oia89\OneDrive\Desktop\DEX-dev-ai-agents>
(venv) PS C:\Users\oia89\OneDrive\Desktop\DEX-dev-ai-agents> python src/agents/rbi_agent_pp_multi.py
[OK] Environment variables loaded

🏗️ Creating new ModelFactory instance...

🔍 Loading environment from: C:\Users\oia89\OneDrive\Desktop\DEX-dev-ai-agents\.env
✨ Environment loaded

🏭 Moon Dev's Model Factory Initialization
══════════════════════════════════════════════════

🔍 Environment Check:
  ├─ GROQ_API_KEY: Found (56 chars)
  ├─ OPENAI_KEY: Found (164 chars)
  ├─ ANTHROPIC_KEY: Found (108 chars)
  ├─ DEEPSEEK_KEY: Not found or empty
  ├─ GROK_API_KEY: Not found or empty
  ├─ GEMINI_KEY: Not found or empty
  ├─ OPENROUTER_API_KEY: Found (73 chars)

🔄 Initializing claude model...
  ├─ Looking for ANTHROPIC_KEY...
  ├─ Found ANTHROPIC_KEY (108 chars)
  ├─ Getting model class for claude...
  ├─ Using model class: ClaudeModel
  ├─ Creating model instance...
  ├─ Default model name: claude-3-5-haiku-latest
✨ Initialized Claude model: claude-3-haiku
  ├─ Model instance created
  ├─ Testing model availability...
  └─ ✨ Successfully initialized claude

🔄 Initializing groq model...
  ├─ Looking for GROQ_API_KEY...
  ├─ Found GROQ_API_KEY (56 chars)
  ├─ Getting model class for groq...
  ├─ Using model class: GroqModel
  ├─ Creating model instance...
  ├─ Default model name: mixtral-8x7b-32768

🌙 Moon Dev's Groq Model Initialization
🔑 API Key validation:
  ├─ Length: 56 chars
  ├─ Contains whitespace: no
  └─ Starts with 'gsk_': yes

📝 Model validation:
  ├─ Requested: qwen/qwen3-32b
  └─ ✅ Model name valid

📡 Parent class initialization...

🔌 Initializing Groq client...
  ├─ API Key length: 56 chars
  ├─ Model name: qwen/qwen3-32b

  ├─ Creating Groq client...
  ├─ ✅ Groq client created
  ├─ Fetching available models from Groq API...
  ├─ Models available from API: ['whisper-large-v3', 'meta-llama/llama-prompt-guard-2-86m', 'openai/gpt-oss-20b', 'moonshotai/kimi-k2-instruct', 'allam-2-7b', 'playai-tts-arabic', 'groq/compound-mini', 'openai/gpt-oss-safeguard-20b', 'openai/gpt-oss-120b', 'playai-tts', 'groq/compound', 'moonshotai/kimi-k2-instruct-0905', 'llama-3.1-8b-instant', 'meta-llama/llama-prompt-guard-2-22m', 'meta-llama/llama-guard-4-12b', 'llama-3.3-70b-versatile', 'qwen/qwen3-32b', 'meta-llama/llama-4-maverick-17b-128e-instruct', 'meta-llama/llama-4-scout-17b-16e-instruct', 'whisper-large-v3-turbo']
  ├─ Testing connection with model: qwen/qwen3-32b
  ├─ ✅ Test response received
  ├─ Response content: <think>
Okay, the user just said "Hello
  ├─ ✨ Groq model initialized: qwen/qwen3-32b
  ├─ Model info: Qwen 3 32B - Production - 32k context
  └─ Pricing: Input $0.50/1M tokens | Output $0.50/1M tokens
✅ Parent class initialized
  ├─ Model instance created
  ├─ Testing model availability...
  └─ ✨ Successfully initialized groq

🔄 Initializing openai model...
  ├─ Looking for OPENAI_KEY...
  ├─ Found OPENAI_KEY (164 chars)
  ├─ Getting model class for openai...
  ├─ Using model class: OpenAIModel
  ├─ Creating model instance...
  ├─ Default model name: gpt-4o
✨ Moon Dev's magic initialized OpenAI model: gpt-4o 🌟
  ├─ Model instance created
  ├─ Testing model availability...
  └─ ✨ Successfully initialized openai

🔄 Initializing gemini model...
  ├─ Looking for GEMINI_KEY...
  └─ ℹ️ GEMINI_KEY not found

🔄 Initializing deepseek model...
  ├─ Looking for DEEPSEEK_KEY...
  └─ ℹ️ DEEPSEEK_KEY not found

🔄 Initializing xai model...
  ├─ Looking for GROK_API_KEY...
  └─ ℹ️ GROK_API_KEY not found

🔄 Initializing openrouter model...
  ├─ Looking for OPENROUTER_API_KEY...
  ├─ Found OPENROUTER_API_KEY (73 chars)
  ├─ Getting model class for openrouter...
  ├─ Using model class: OpenRouterModel
  ├─ Creating model instance...
  ├─ Default model name: x-ai/grok-code-fast-1

🌙 Moon Dev's OpenRouter Model Initialization
🔑 API Key validation:
  ├─ Length: 73 chars
  ├─ Contains whitespace: no
  └─ Starts with 'sk-or-': yes

📝 Model validation:
  ├─ Requested: google/gemini-2.5-flash
  └─ ✅ Model name recognized

📡 Parent class initialization...

🔌 Initializing OpenRouter client...
  ├─ API Key length: 73 chars
  ├─ Model name: google/gemini-2.5-flash

  ├─ Creating OpenRouter client (via OpenAI SDK)...
  ├─ ✅ OpenRouter client created
  ├─ Testing connection with model: google/gemini-2.5-flash
  ├─ ✅ Test response received
  ├─ Response content: Hi! How can I help you today?
  ├─ ✨ OpenRouter model initialized: google/gemini-2.5-flash
  ├─ Model info: Gemini 2.5 Flash - Fast multimodal - 1M context
  └─ Pricing: Input $0.10/1M tokens | Output $0.40/1M tokens
✅ Parent class initialized
  ├─ Model instance created
  ├─ Testing model availability...
  └─ ✨ Successfully initialized openrouter

🔄 Initializing Ollama model...
❌ Could not connect to Ollama API - is the server running?
💡 Start the server with: ollama serve
❌ Failed to initialize Ollama: HTTPConnectionPool(host='localhost', port=11434): Max retries exceeded with url: /api/tags (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x000001277E6306E0>: Failed to establish a new connection: [WinError 10061] No connection could be made because the target machine actively refused it'))

══════════════════════════════════════════════════
📊 Initialization Summary:
  ├─ Models attempted: 8
  ├─ Models initialized: 4
  └─ Available models: ['claude', 'groq', 'openai', 'openrouter']

🤖 Available AI Models:
  ├─ claude: claude-3-haiku
  ├─ groq: qwen/qwen3-32b
  ├─ openai: gpt-4o
  ├─ openrouter: google/gemini-2.5-flash
  └─ Moon Dev's Model Factory Ready! 🌙
[OK] Successfully imported model_factory

============================================================
🛡️  SYSTEM STARTUP VALIDATION
============================================================

  ✅ RESEARCH             | openrouter   | x-ai/grok-code-fast-1
  ✅ PACKAGE              | openrouter   | x-ai/grok-code-fast-1
  ✅ BACKTEST_MODEL_0     | claude       | claude-sonnet-4-5
  ✅ BACKTEST_MODEL_1     | openrouter   | x-ai/grok-code-fast-1
  ✅ BACKTEST_MODEL_2     | groq         | llama-3.3-70b-versatile
  ✅ BACKTEST_MODEL_3     | claude       | claude-sonnet-4-5
  ✅ BACKTEST_MODEL_4     | openrouter   | x-ai/grok-code-fast-1
  ✅ BACKTEST_MODEL_5     | groq         | llama-3.3-70b-versatile
  ✅ BACKTEST_MODEL_6     | claude       | claude-sonnet-4-5
  ✅ BACKTEST_MODEL_7     | openrouter   | x-ai/grok-code-fast-1
  ✅ BACKTEST_MODEL_8     | groq         | llama-3.3-70b-versatile
  ✅ DEBUG_MODEL_0        | openrouter   | x-ai/grok-code-fast-1
  ✅ DEBUG_MODEL_1        | openrouter   | x-ai/grok-code-fast-1
  ✅ DEBUG_MODEL_2        | openrouter   | x-ai/grok-code-fast-1
  ✅ DEBUG_MODEL_3        | openrouter   | x-ai/grok-code-fast-1
  ✅ DEBUG_MODEL_4        | openrouter   | x-ai/grok-code-fast-1
  ✅ DEBUG_MODEL_5        | openrouter   | x-ai/grok-code-fast-1
  ✅ DEBUG_MODEL_6        | openrouter   | x-ai/grok-code-fast-1
  ✅ DEBUG_MODEL_7        | openrouter   | x-ai/grok-code-fast-1
  ✅ DEBUG_MODEL_8        | openrouter   | x-ai/grok-code-fast-1
  ✅ OPTIMIZE_MODEL_0     | openrouter   | x-ai/grok-code-fast-1
  ✅ OPTIMIZE_MODEL_1     | openrouter   | x-ai/grok-code-fast-1
  ✅ OPTIMIZE_MODEL_2     | openrouter   | x-ai/grok-code-fast-1
  ✅ OPTIMIZE_MODEL_3     | openrouter   | x-ai/grok-code-fast-1
  ✅ OPTIMIZE_MODEL_4     | openrouter   | x-ai/grok-code-fast-1
  ✅ OPTIMIZE_MODEL_5     | openrouter   | x-ai/grok-code-fast-1
  ✅ OPTIMIZE_MODEL_6     | openrouter   | x-ai/grok-code-fast-1
  ✅ OPTIMIZE_MODEL_7     | openrouter   | x-ai/grok-code-fast-1
  ✅ OPTIMIZE_MODEL_8     | openrouter   | x-ai/grok-code-fast-1

============================================================
✅ ALL CONFIGURATIONS VALID - READY TO START
============================================================


============================================================
🌟 Moon Dev's RBI AI v3.0 PARALLEL PROCESSOR + MULTI-DATA 🚀
============================================================

📅 Date: 11_11_2025
🎯 Target Return: 50%
🔀 Max Parallel Threads: 9
🐍 Conda env: tflow
📂 Data dir: C:\Users\oia89\OneDrive\Desktop\DEX-dev-ai-agents\src\data\rbi_pp_multi
📝 Ideas file: C:\Users\oia89\OneDrive\Desktop\DEX-dev-ai-agents\src\data\rbi_pp_multi\ideas.txt


============================================================
📁 STRATEGY SOURCE: FILES FROM FOLDER
📂 Folder: C:\Users\oia89\OneDrive\Desktop\DEX-dev-ai-agents\src\data\web_search_research\final_strategies
📊 Found 12 strategy files (.md/.txt)
============================================================


🔄 CONTINUOUS QUEUE MODE ACTIVATED
⏰ Monitoring strategy files in folder every 1 second
🧵 9 worker threads ready

✅ Idea monitor thread started
✅ 9 worker threads started (IDs 00-08)

📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
🆕 NEW IDEA QUEUED: # The Squeeze (Volatility Contraction) Strategy

A strategy that identifies peri...

🚀 Thread 00 starting: # The Squeeze (Volatility Contraction) Strategy

A strategy that identifies peri...
🆕 NEW IDEA QUEUED: # Overbought/Oversold Conditions Strategy

A strategy that capitalizes on price ...

🚀 Thread 01 starting: # Overbought/Oversold Conditions Strategy

A strategy that capitalizes on price ...
🆕 NEW IDEA QUEUED: # W-Bottoms and M-Tops Patterns Strategy

A reversal pattern strategy that ident...

🚀 Thread 02 starting: # W-Bottoms and M-Tops Patterns Strategy

A reversal pattern strategy that ident...
🆕 NEW IDEA QUEUED: # Bollinger Band Breakouts Strategy

A momentum strategy that trades decisive pr...

🚀 Thread 03 starting: # Bollinger Band Breakouts Strategy

A momentum strategy that trades decisive pr...
🆕 NEW IDEA QUEUED: # Bollinger Band Swing Trading Strategy

A swing trading approach that uses the ...

🚀 Thread 04 starting: # Bollinger Band Swing Trading Strategy

A swing trading approach that uses the ...
🆕 NEW IDEA QUEUED: # Bollinger Band Trend Following Strategy

A trend-following strategy that enter...

🚀 Thread 05 starting: # Bollinger Band Trend Following Strategy

A trend-following strategy that enter...
🆕 NEW IDEA QUEUED: # Bollinger Band Squeeze Breakout Strategy

A specialized breakout strategy that...

🚀 Thread 06 starting: # Bollinger Band Squeeze Breakout Strategy

A specialized breakout strategy that...
🆕 NEW IDEA QUEUED: # Bollinger Band Mean Reversion Strategy

A mean reversion strategy that trades ...

🚀 Thread 07 starting: # Bollinger Band Mean Reversion Strategy

A mean reversion strategy that trades ...
🆕 NEW IDEA QUEUED: # Bollinger Band with Volume Profile Strategy

A confluence strategy that combin...

🚀 Thread 08 starting: # Bollinger Band with Volume Profile Strategy

A confluence strategy that combin...
🆕 NEW IDEA QUEUED: # Bollinger Bands + RSI Divergence Setup

A multi-indicator strategy that combin...
🆕 NEW IDEA QUEUED: # Bollinger Bands + MACD + Volume Setup

A momentum strategy combining Bollinger...
[T00] 🚀 Starting processing
[T00] 🔍 RESEARCH: Starting analysis...
🆕 NEW IDEA QUEUED: # Bollinger Bands + Moving Average + Stochastic Setup

A trend and momentum comb...
🆕 NEW IDEA QUEUED: After H&S breakdown, gave a good follow through selling before reversing...
🆕 NEW IDEA QUEUED: LOw ADX signals coiled volatility....
🆕 NEW IDEA QUEUED: ADX chop. It's a buildup....
🆕 NEW IDEA QUEUED: ADX model breakout strategy using:...
🆕 NEW IDEA QUEUED: ADX Volatility = open–low difference...
🆕 NEW IDEA QUEUED: ADX Breakout level = low + (3.3 × volatility)...
🆕 NEW IDEA QUEUED: ADX Stop entries only...
🆕 NEW IDEA QUEUED: ADX Entry filter: 8am–3pm...
🆕 NEW IDEA QUEUED: ADX Exit: when ADX > 40 or after time limit...
🆕 NEW IDEA QUEUED: ADX Calibration...
[T01] 🚀 Starting processing
[T01] 🔍 RESEARCH: Starting analysis...
🆕 NEW IDEA QUEUED: ADX multiple markets to find robust parameters....
🆕 NEW IDEA QUEUED: ADX overfitting to one instrument....
🆕 NEW IDEA QUEUED: recent and current ADX strength....
🆕 NEW IDEA QUEUED: ATR-based, trailing stops, volatility brackets...
🆕 NEW IDEA QUEUED: MCSO>=50...
🆕 NEW IDEA QUEUED: Triple Exponential MA (distance from close)....
🆕 NEW IDEA QUEUED: MA slope (20–50 periods)....
🆕 NEW IDEA QUEUED: Money Flow Index....
🆕 NEW IDEA QUEUED: MFI filters...
🆕 NEW IDEA QUEUED: EMA Bollinger...
🆕 NEW IDEA QUEUED: Supertrend plus Rate of change...
[T02] 🚀 Starting processing
[T02] 🔍 RESEARCH: Starting analysis...
🆕 NEW IDEA QUEUED: https://www.youtube.com/watch?v=dlvIAsoKAuE...
🆕 NEW IDEA QUEUED: WMA + EMA...
🆕 NEW IDEA QUEUED: https://www.youtube.com/watch?v=S0EO91bJqDQ...
🆕 NEW IDEA QUEUED: CCI + Williams percentage range...
🆕 NEW IDEA QUEUED: www.youtube.com/watch?si=3n25Ie6TIBZC4Tm6&v=T9ErBgkNcEE&feature=youtu.be...
[T03] 🚀 Starting processing
[T03] 🔍 RESEARCH: Starting analysis...
[T04] 🚀 Starting processing
[T04] 🔍 RESEARCH: Starting analysis...
[T05] 🚀 Starting processing
[T05] 🔍 RESEARCH: Starting analysis...
[T06] 🚀 Starting processing
[T06] 🔍 RESEARCH: Starting analysis...
[T07] 🚀 Starting processing
[T07] 🔍 RESEARCH: Starting analysis...
[T08] 🚀 Starting processing
[T08] 🔍 RESEARCH: Starting analysis...

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
🔄 Reinitializing openrouter with model x-ai/grok-code-fast-1...

🌙 Moon Dev's OpenRouter Model Initialization
🔑 API Key validation:
  ├─ Length: 73 chars
  ├─ Contains whitespace: no
  └─ Starts with 'sk-or-': yes

📝 Model validation:
  ├─ Requested: x-ai/grok-code-fast-1
  └─ ⚠️ Model not in predefined list (will still try to use it)
  💡 OpenRouter supports 200+ models - see https://openrouter.ai/docs

📡 Parent class initialization...

🔌 Initializing OpenRouter client...
  ├─ API Key length: 73 chars
  ├─ Model name: x-ai/grok-code-fast-1

  ├─ Creating OpenRouter client (via OpenAI SDK)...

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
🔄 Reinitializing openrouter with model x-ai/grok-code-fast-1...

🌙 Moon Dev's OpenRouter Model Initialization
🔑 API Key validation:
  ├─ Length: 73 chars
  ├─ Contains whitespace: no
  └─ Starts with 'sk-or-': yes

📝 Model validation:
  ├─ Requested: x-ai/grok-code-fast-1
  └─ ⚠️ Model not in predefined list (will still try to use it)
  💡 OpenRouter supports 200+ models - see https://openrouter.ai/docs

📡 Parent class initialization...

🔌 Initializing OpenRouter client...
  ├─ API Key length: 73 chars
  ├─ Model name: x-ai/grok-code-fast-1

  ├─ Creating OpenRouter client (via OpenAI SDK)...
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
  ├─ ✅ OpenRouter client created
  ├─ Testing connection with model: x-ai/grok-code-fast-1

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
🔄 Reinitializing openrouter with model x-ai/grok-code-fast-1...

🌙 Moon Dev's OpenRouter Model Initialization
🔑 API Key validation:
  ├─ Length: 73 chars
  ├─ Contains whitespace: no
  └─ Starts with 'sk-or-': yes

📝 Model validation:
  ├─ Requested: x-ai/grok-code-fast-1
  └─ ⚠️ Model not in predefined list (will still try to use it)
  💡 OpenRouter supports 200+ models - see https://openrouter.ai/docs

📡 Parent class initialization...

🔌 Initializing OpenRouter client...
  ├─ API Key length: 73 chars
  ├─ Model name: x-ai/grok-code-fast-1

  ├─ Creating OpenRouter client (via OpenAI SDK)...
  ├─ ✅ OpenRouter client created
  ├─ Testing connection with model: x-ai/grok-code-fast-1

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
🔄 Reinitializing openrouter with model x-ai/grok-code-fast-1...

🌙 Moon Dev's OpenRouter Model Initialization
🔑 API Key validation:
  ├─ Length: 73 chars
  ├─ Contains whitespace: no
  └─ Starts with 'sk-or-': yes

📝 Model validation:
  ├─ Requested: x-ai/grok-code-fast-1
  └─ ⚠️ Model not in predefined list (will still try to use it)
  💡 OpenRouter supports 200+ models - see https://openrouter.ai/docs

📡 Parent class initialization...

🔌 Initializing OpenRouter client...
  ├─ API Key length: 73 chars
  ├─ Model name: x-ai/grok-code-fast-1

  ├─ Creating OpenRouter client (via OpenAI SDK)...
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
  ├─ ✅ OpenRouter client created
  ├─ Testing connection with model: x-ai/grok-code-fast-1

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
🔄 Reinitializing openrouter with model x-ai/grok-code-fast-1...

🌙 Moon Dev's OpenRouter Model Initialization
🔑 API Key validation:
  ├─ Length: 73 chars
  ├─ Contains whitespace: no
  └─ Starts with 'sk-or-': yes

📝 Model validation:
  ├─ Requested: x-ai/grok-code-fast-1
  └─ ⚠️ Model not in predefined list (will still try to use it)
  💡 OpenRouter supports 200+ models - see https://openrouter.ai/docs

📡 Parent class initialization...

🔌 Initializing OpenRouter client...
  ├─ API Key length: 73 chars
  ├─ Model name: x-ai/grok-code-fast-1

  ├─ Creating OpenRouter client (via OpenAI SDK)...
  ├─ ✅ OpenRouter client created
  ├─ Testing connection with model: x-ai/grok-code-fast-1

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
🔄 Reinitializing openrouter with model x-ai/grok-code-fast-1...

🌙 Moon Dev's OpenRouter Model Initialization
🔑 API Key validation:
  ├─ Length: 73 chars
  ├─ Contains whitespace: no
  └─ Starts with 'sk-or-': yes

📝 Model validation:
  ├─ Requested: x-ai/grok-code-fast-1
  └─ ⚠️ Model not in predefined list (will still try to use it)
  💡 OpenRouter supports 200+ models - see https://openrouter.ai/docs

📡 Parent class initialization...

🔌 Initializing OpenRouter client...
  ├─ API Key length: 73 chars
  ├─ Model name: x-ai/grok-code-fast-1

  ├─ Creating OpenRouter client (via OpenAI SDK)...
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
  ├─ ✅ OpenRouter client created
  ├─ Testing connection with model: x-ai/grok-code-fast-1

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
🔄 Reinitializing openrouter with model x-ai/grok-code-fast-1...

🌙 Moon Dev's OpenRouter Model Initialization
🔑 API Key validation:
  ├─ Length: 73 chars
  ├─ Contains whitespace: no
  └─ Starts with 'sk-or-': yes

📝 Model validation:
  ├─ Requested: x-ai/grok-code-fast-1
  └─ ⚠️ Model not in predefined list (will still try to use it)
  💡 OpenRouter supports 200+ models - see https://openrouter.ai/docs

📡 Parent class initialization...

🔌 Initializing OpenRouter client...
  ├─ API Key length: 73 chars
  ├─ Model name: x-ai/grok-code-fast-1

  ├─ Creating OpenRouter client (via OpenAI SDK)...
  ├─ ✅ OpenRouter client created
  ├─ Testing connection with model: x-ai/grok-code-fast-1

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
🔄 Reinitializing openrouter with model x-ai/grok-code-fast-1...

🌙 Moon Dev's OpenRouter Model Initialization
🔑 API Key validation:
  ├─ Length: 73 chars
  ├─ Contains whitespace: no
  └─ Starts with 'sk-or-': yes

📝 Model validation:
  ├─ Requested: x-ai/grok-code-fast-1
  └─ ⚠️ Model not in predefined list (will still try to use it)
  💡 OpenRouter supports 200+ models - see https://openrouter.ai/docs

📡 Parent class initialization...

🔌 Initializing OpenRouter client...
  ├─ API Key length: 73 chars
  ├─ Model name: x-ai/grok-code-fast-1

  ├─ Creating OpenRouter client (via OpenAI SDK)...
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
  ├─ ✅ OpenRouter client created
  ├─ Testing connection with model: x-ai/grok-code-fast-1

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
🔄 Reinitializing openrouter with model x-ai/grok-code-fast-1...

🌙 Moon Dev's OpenRouter Model Initialization
🔑 API Key validation:
  ├─ Length: 73 chars
  ├─ Contains whitespace: no
  └─ Starts with 'sk-or-': yes

📝 Model validation:
  ├─ Requested: x-ai/grok-code-fast-1
  └─ ⚠️ Model not in predefined list (will still try to use it)
  💡 OpenRouter supports 200+ models - see https://openrouter.ai/docs

📡 Parent class initialization...

🔌 Initializing OpenRouter client...
  ├─ API Key length: 73 chars
  ├─ Model name: x-ai/grok-code-fast-1

  ├─ Creating OpenRouter client (via OpenAI SDK)...
  ├─ ✅ OpenRouter client created
  ├─ Testing connection with model: x-ai/grok-code-fast-1
📊 Status: 9 active | 29 queued | 0 completed | 0 targets hit
  ├─ ✅ Test response received
  ├─ Response content: Hello! I'm Grok, created by xAI
  ├─ ✨ OpenRouter model initialized: x-ai/grok-code-fast-1
  ├─ Model info: Custom model via OpenRouter
  └─ Pricing: Input See openrouter.ai/docs | Output See openrouter.ai/docs
✅ Parent class initialized
✨ Successfully reinitialized with new model
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
  ├─ ✅ OpenRouter client created
  ├─ Testing connection with model: x-ai/grok-code-fast-1
  ├─ ✅ Test response received
  ├─ Response content: Hello! How can I help you today?
  ├─ ✨ OpenRouter model initialized: x-ai/grok-code-fast-1
  ├─ Model info: Custom model via OpenRouter
  └─ Pricing: Input See openrouter.ai/docs | Output See openrouter.ai/docs
✅ Parent class initialized
✨ Successfully reinitialized with new model
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
  ├─ ✅ Test response received
  ├─ Response content: Hello! How can I assist you today? If
  ├─ ✨ OpenRouter model initialized: x-ai/grok-code-fast-1
  ├─ Model info: Custom model via OpenRouter
  └─ Pricing: Input See openrouter.ai/docs | Output See openrouter.ai/docs
✅ Parent class initialized
✨ Successfully reinitialized with new model
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
  ├─ ✅ Test response received
  ├─ Response content: Hello! How's it going? What can I
  ├─ ✨ OpenRouter model initialized: x-ai/grok-code-fast-1
  ├─ Model info: Custom model via OpenRouter
  └─ Pricing: Input See openrouter.ai/docs | Output See openrouter.ai/docs
✅ Parent class initialized
✨ Successfully reinitialized with new model
  ├─ ✅ Test response received
  ├─ Response content: Hello! How can I help you today?
  ├─ ✨ OpenRouter model initialized: x-ai/grok-code-fast-1
  ├─ Model info: Custom model via OpenRouter
  └─ Pricing: Input See openrouter.ai/docs | Output See openrouter.ai/docs
✅ Parent class initialized
✨ Successfully reinitialized with new model
  ├─ ✅ Test response received
  ├─ Response content: Hello! How can I assist you today?
  ├─ ✨ OpenRouter model initialized: x-ai/grok-code-fast-1
  ├─ Model info: Custom model via OpenRouter
  └─ Pricing: Input See openrouter.ai/docs | Output See openrouter.ai/docs
✅ Parent class initialized
✨ Successfully reinitialized with new model
  ├─ ✅ Test response received
  ├─ Response content: Hello! How can I help you today?
  ├─ ✨ OpenRouter model initialized: x-ai/grok-code-fast-1
  ├─ Model info: Custom model via OpenRouter
  └─ Pricing: Input See openrouter.ai/docs | Output See openrouter.ai/docs
✅ Parent class initialized
✨ Successfully reinitialized with new model
  ├─ ✅ Test response received
  ├─ Response content: Hello! How can I assist you today? Whether
  ├─ ✨ OpenRouter model initialized: x-ai/grok-code-fast-1
  ├─ Model info: Custom model via OpenRouter
  └─ Pricing: Input See openrouter.ai/docs | Output See openrouter.ai/docs
✅ Parent class initialized
✨ Successfully reinitialized with new model
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
  ├─ ✅ Test response received
  ├─ Response content: Hello! How can I help you today?
  ├─ ✨ OpenRouter model initialized: x-ai/grok-code-fast-1
  ├─ Model info: Custom model via OpenRouter
  └─ Pricing: Input See openrouter.ai/docs | Output See openrouter.ai/docs
✅ Parent class initialized
✨ Successfully reinitialized with new model
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 29 queued | 0 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 29 queued | 0 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 29 queued | 0 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T06] ✅ Strategy: SqueezeRetracement
[T06] 📝 Logged processed idea: SqueezeRetracement
[T06] 📊 BACKTEST: Creating backtest code...
[T06] Using model: claude/claude-sonnet-4-5
📊 Status: 9 active | 29 queued | 0 completed | 0 targets hit

🔍 Requesting model: claude (claude-sonnet-4-5)
🔄 Reinitializing claude with model claude-sonnet-4-5...
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T03] ✅ Strategy: VolumetricBreakout
[T03] 📝 Logged processed idea: VolumetricBreakout
[T03] 📊 BACKTEST: Creating backtest code...
[T03] Using model: claude/claude-sonnet-4-5
✨ Initialized Claude model: claude-sonnet-4-5
✨ Successfully reinitialized with new model

🔍 Requesting model: claude (claude-sonnet-4-5)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T07] ✅ Strategy: VolatilityReversion
[T07] 📝 Logged processed idea: VolatilityReversion
[T07] 📊 BACKTEST: Creating backtest code...
[T07] Using model: openrouter/x-ai/grok-code-fast-1

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 29 queued | 0 completed | 0 targets hit
[T01] ✅ Strategy: DivergentReversal
[T00] ✅ Strategy: SqueezeBreakout
[T01] 📝 Logged processed idea: DivergentReversal
[T01] 📊 BACKTEST: Creating backtest code...
[T01] Using model: openrouter/x-ai/grok-code-fast-1
[T00] 📝 Logged processed idea: SqueezeBreakout
[T00] 📊 BACKTEST: Creating backtest code...
[T00] Using model: claude/claude-sonnet-4-5
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)

🔍 Requesting model: claude (claude-sonnet-4-5)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 29 queued | 0 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T02] ✅ Strategy: VolatilityReversal
[T02] 📝 Logged processed idea: VolatilityReversal
[T02] 📊 BACKTEST: Creating backtest code...
[T02] Using model: groq/llama-3.3-70b-versatile
[T08] ✅ Strategy: VolumetricReversal
[T08] 📝 Logged processed idea: VolumetricReversal
[T08] 📊 BACKTEST: Creating backtest code...
[T08] Using model: groq/llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: groq (llama-3.3-70b-versatile)
🔄 Reinitializing groq with model llama-3.3-70b-versatile...

🌙 Moon Dev's Groq Model Initialization
🔑 API Key validation:
  ├─ Length: 56 chars
  ├─ Contains whitespace: no
  └─ Starts with 'gsk_': yes

📝 Model validation:
  ├─ Requested: llama-3.3-70b-versatile
  └─ ✅ Model name valid

📡 Parent class initialization...

🔌 Initializing Groq client...
  ├─ API Key length: 56 chars
  ├─ Model name: llama-3.3-70b-versatile

  ├─ Creating Groq client...

🔍 Requesting model: groq (llama-3.3-70b-versatile)
🔄 Reinitializing groq with model llama-3.3-70b-versatile...

🌙 Moon Dev's Groq Model Initialization
🔑 API Key validation:
  ├─ Length: 56 chars
  ├─ Contains whitespace: no
  └─ Starts with 'gsk_': yes

📝 Model validation:
  ├─ Requested: llama-3.3-70b-versatile
  └─ ✅ Model name valid

📡 Parent class initialization...

🔌 Initializing Groq client...
  ├─ API Key length: 56 chars
  ├─ Model name: llama-3.3-70b-versatile

  ├─ Creating Groq client...
  ├─ ✅ Groq client created
  ├─ Fetching available models from Groq API...
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
  ├─ ✅ Groq client created
  ├─ Fetching available models from Groq API...
  ├─ Models available from API: ['openai/gpt-oss-safeguard-20b', 'meta-llama/llama-guard-4-12b', 'openai/gpt-oss-120b', 'meta-llama/llama-prompt-guard-2-86m', 'playai-tts-arabic', 'meta-llama/llama-4-scout-17b-16e-instruct', 'moonshotai/kimi-k2-instruct', 'moonshotai/kimi-k2-instruct-0905', 'llama-3.1-8b-instant', 'playai-tts', 'meta-llama/llama-prompt-guard-2-22m', 'openai/gpt-oss-20b', 'whisper-large-v3', 'groq/compound-mini', 'llama-3.3-70b-versatile', 'groq/compound', 'allam-2-7b', 'whisper-large-v3-turbo', 'meta-llama/llama-4-maverick-17b-128e-instruct', 'qwen/qwen3-32b']
  ├─ Testing connection with model: llama-3.3-70b-versatile
📊 Status: 9 active | 29 queued | 0 completed | 0 targets hit
  ├─ Models available from API: ['llama-3.1-8b-instant', 'meta-llama/llama-prompt-guard-2-22m', 'meta-llama/llama-prompt-guard-2-86m', 'meta-llama/llama-4-scout-17b-16e-instruct', 'moonshotai/kimi-k2-instruct', 'playai-tts-arabic', 'moonshotai/kimi-k2-instruct-0905', 'whisper-large-v3', 'whisper-large-v3-turbo', 'playai-tts', 'meta-llama/llama-guard-4-12b', 'openai/gpt-oss-20b', 'llama-3.3-70b-versatile', 'qwen/qwen3-32b', 'openai/gpt-oss-120b', 'openai/gpt-oss-safeguard-20b', 'allam-2-7b', 'meta-llama/llama-4-maverick-17b-128e-instruct', 'groq/compound', 'groq/compound-mini']
  ├─ Testing connection with model: llama-3.3-70b-versatile
  ├─ ✅ Test response received
  ├─ Response content: Hello. How can I help you today?
  ├─ ✨ Groq model initialized: llama-3.3-70b-versatile
  ├─ Model info: Llama 3.3 70B Versatile - Production - 128k context
  └─ Pricing: Input $0.70/1M tokens | Output $0.90/1M tokens
✅ Parent class initialized
✨ Successfully reinitialized with new model
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
  ├─ ✅ Test response received
  ├─ Response content: Hello. How can I assist you today?
  ├─ ✨ Groq model initialized: llama-3.3-70b-versatile
  ├─ Model info: Llama 3.3 70B Versatile - Production - 128k context
  └─ Pricing: Input $0.70/1M tokens | Output $0.90/1M tokens
✅ Parent class initialized
✨ Successfully reinitialized with new model
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3365 tokens
   💡 Skipping this model for this request...
[T08] ❌ Model error: Model returned None response
[T08] 🔄 Attempt 1 failed, trying fallback...

[T08] 🔄 Attempting fallback models for backtest...
[T08]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
[T04] ✅ Strategy: VolatilitySwing
[T04] 📝 Logged processed idea: VolatilitySwing
[T04] 📊 BACKTEST: Creating backtest code...
[T04] Using model: openrouter/x-ai/grok-code-fast-1
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: groq (llama-3.3-70b-versatile)
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3365 tokens
   💡 Skipping this model for this request...
[T08] ❌ Model error: Model returned None response
[T08] 🔄 Attempt 2 failed, trying fallback...

[T08] 🔄 Attempting fallback models for backtest...
[T08]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T05] ✅ Strategy: RecoilBreakout
[T05] 📝 Logged processed idea: RecoilBreakout
[T05] 📊 BACKTEST: Creating backtest code...
[T05] Using model: groq/llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 29 queued | 0 completed | 0 targets hit

🔍 Requesting model: groq (llama-3.3-70b-versatile)
[T02] 🔥 Backtest code saved
[T02] 📦 PACKAGE: Checking imports...
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 2958 tokens
   💡 Skipping this model for this request...
[T05] ❌ Model error: Model returned None response
[T05] 🔄 Attempt 1 failed, trying fallback...

[T05] 🔄 Attempting fallback models for backtest...
[T05]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)

🔍 Requesting model: groq (llama-3.3-70b-versatile)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T07] 🔥 Backtest code saved
[T07] 📦 PACKAGE: Checking imports...

🔍 Requesting model: groq (llama-3.3-70b-versatile)

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3365 tokens
   💡 Skipping this model for this request...
[T08] ❌ Model error: Model returned None response
[T08] ❌ All model attempts failed for backtest
[T08] ❌ FATAL ERROR: 🚨 Could not initialize any model for backtest after 3 attempts!

============================================================
✅ Thread 08 COMPLETED (1 total) - 49.5s
❌ Failed: 🚨 Could not initialize any model for backtest after 3 attempts!
============================================================


🚀 Thread 08 starting: # Bollinger Bands + RSI Divergence Setup

A multi-indicator strategy that combin...
[T08] 🚀 Starting processing
[T08] 🔍 RESEARCH: Starting analysis...
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 28 queued | 1 completed | 0 targets hit

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 2958 tokens
   💡 Skipping this model for this request...
[T05] ❌ Model error: Model returned None response
[T05] 🔄 Attempt 2 failed, trying fallback...

[T05] 🔄 Attempting fallback models for backtest...
[T05]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: groq (llama-3.3-70b-versatile)
📊 Status: 9 active | 28 queued | 1 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T01] 🔥 Backtest code saved
[T01] 📦 PACKAGE: Checking imports...

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 28 queued | 1 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 2958 tokens
   💡 Skipping this model for this request...
[T05] ❌ Model error: Model returned None response
[T05] ❌ All model attempts failed for backtest
[T05] ❌ FATAL ERROR: 🚨 Could not initialize any model for backtest after 3 attempts!

============================================================
✅ Thread 05 COMPLETED (2 total) - 61.7s
❌ Failed: 🚨 Could not initialize any model for backtest after 3 attempts!
============================================================


🚀 Thread 05 starting: # Bollinger Bands + MACD + Volume Setup

A momentum strategy combining Bollinger...
[T05] 🚀 Starting processing
[T05] 🔍 RESEARCH: Starting analysis...
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 27 queued | 2 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T07] 📦 Package check complete
[T07] 🚀 EXECUTE: Attempt 1/10
[T07] 🚀 Executing: VolatilityReversion
📊 Status: 9 active | 27 queued | 2 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T07] ❌ Backtest failed: 1
[T07] 🔧 DEBUG #1: Fixing errors...
[T07] Debug with: openrouter/x-ai/grok-code-fast-1

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T02] 📦 Package check complete
[T02] 🚀 EXECUTE: Attempt 1/10
[T02] 🚀 Executing: VolatilityReversal
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 27 queued | 2 completed | 0 targets hit
[T06] 🔥 Backtest code saved
[T06] 📦 PACKAGE: Checking imports...
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T03] 🔥 Backtest code saved
[T03] 📦 PACKAGE: Checking imports...
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 27 queued | 2 completed | 0 targets hit
[T02] ❌ Backtest failed: 1
[T02] 🔧 DEBUG #1: Fixing errors...
[T02] Debug with: openrouter/x-ai/grok-code-fast-1
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T04] 🔥 Backtest code saved
[T04] 📦 PACKAGE: Checking imports...

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
[T01] 📦 Package check complete
[T01] 🚀 EXECUTE: Attempt 1/10
[T01] 🚀 Executing: DivergentReversal

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T00] 🔥 Backtest code saved
[T00] 📦 PACKAGE: Checking imports...

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T01] ❌ Backtest failed: 1
[T01] 🔧 DEBUG #1: Fixing errors...
[T01] Debug with: openrouter/x-ai/grok-code-fast-1
[T08] ✅ Strategy: DivergentReversal
[T08] 📝 Logged processed idea: DivergentReversal
[T08] 📊 BACKTEST: Creating backtest code...
[T08] Using model: groq/llama-3.3-70b-versatile
📊 Status: 9 active | 27 queued | 2 completed | 0 targets hit

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: groq (llama-3.3-70b-versatile)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3042 tokens
   💡 Skipping this model for this request...
[T08] ❌ Model error: Model returned None response
[T08] 🔄 Attempt 1 failed, trying fallback...

[T08] 🔄 Attempting fallback models for backtest...
[T08]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 27 queued | 2 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: groq (llama-3.3-70b-versatile)
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3042 tokens
   💡 Skipping this model for this request...
[T08] ❌ Model error: Model returned None response
[T08] 🔄 Attempt 2 failed, trying fallback...

[T08] 🔄 Attempting fallback models for backtest...
[T08]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T06] 📦 Package check complete
[T06] 🚀 EXECUTE: Attempt 1/10
[T06] 🚀 Executing: SqueezeRetracement
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: groq (llama-3.3-70b-versatile)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3042 tokens
   💡 Skipping this model for this request...
[T08] ❌ Model error: Model returned None response
[T08] ❌ All model attempts failed for backtest
[T08] ❌ FATAL ERROR: 🚨 Could not initialize any model for backtest after 3 attempts!

============================================================
✅ Thread 08 COMPLETED (3 total) - 45.3s
❌ Failed: 🚨 Could not initialize any model for backtest after 3 attempts!
============================================================


🚀 Thread 08 starting: # Bollinger Bands + Moving Average + Stochastic Setup

A trend and momentum comb...
[T08] 🚀 Starting processing
[T08] 🔍 RESEARCH: Starting analysis...
📊 Status: 9 active | 26 queued | 3 completed | 0 targets hit
[T07] 🔧 Debug iteration 1 complete
[T07] 🚀 EXECUTE: Attempt 2/10
[T07] 🚀 Executing: VolatilityReversion

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T03] 📦 Package check complete
[T03] 🚀 EXECUTE: Attempt 1/10
[T03] 🚀 Executing: VolumetricBreakout
[T03] ❌ Backtest failed: 1
[T03] 🔧 DEBUG #1: Fixing errors...
[T03] Debug with: openrouter/x-ai/grok-code-fast-1

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T07] ❌ Backtest failed: 1
[T07] 🔧 DEBUG #2: Fixing errors...
[T07] Debug with: openrouter/x-ai/grok-code-fast-1
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
[T06] ✅ Backtest executed in 5.64s!
[T06] 🎉 BACKTEST SUCCESSFUL!
[T06] 📊 Extracted 7/8 stats
[T06] ⚠️ Return 0.47231% ≤ 1.0% threshold - not saving
[T06] 🔍 Checking for multi-data test results...
[T06] ⚠️ No multi-data results found at C:\Users\oia89\OneDrive\Desktop\DEX-dev-ai-agents\src\data\rbi_pp_multi\11_11_2025\backtests_package\results\SqueezeRetracement.csv
[T06] 📊 Return: 0.47231% | Target: 50%
[T06] 📈 Need 49.52769% more - Starting optimization
[T06] 🎯 OPTIMIZE #1: 0.47231% → 50%
[T06] Optimize with: openrouter/x-ai/grok-code-fast-1
[T04] 📦 Package check complete
[T04] 🚀 EXECUTE: Attempt 1/10
[T04] 🚀 Executing: VolatilitySwing

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 26 queued | 3 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T04] ❌ Backtest failed: 1
[T04] 🔧 DEBUG #1: Fixing errors...
[T04] Debug with: openrouter/x-ai/grok-code-fast-1

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T00] 📦 Package check complete
[T00] 🚀 EXECUTE: Attempt 1/10
[T00] 🚀 Executing: SqueezeBreakout
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 26 queued | 3 completed | 0 targets hit
[T01] 🔧 Debug iteration 1 complete
[T01] 🚀 EXECUTE: Attempt 2/10
[T01] 🚀 Executing: DivergentReversal
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T01] ❌ Backtest failed: 1
[T01] 🔧 DEBUG #2: Fixing errors...
[T01] Debug with: openrouter/x-ai/grok-code-fast-1
[T02] 🔧 Debug iteration 1 complete
[T02] 🚀 EXECUTE: Attempt 2/10
[T02] 🚀 Executing: VolatilityReversal

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 26 queued | 3 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T05] ✅ Strategy: FractalBreakout
[T05] 📝 Logged processed idea: FractalBreakout
[T05] 📊 BACKTEST: Creating backtest code...
[T05] Using model: groq/llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: groq (llama-3.3-70b-versatile)
[T00] ✅ Backtest executed in 8.60s!
[T00] 🎉 BACKTEST SUCCESSFUL!
[T00] 📊 Extracted 7/8 stats
[T00] 💾 Saved to working & final! Return: 2.01%
[T00] ✅ Logged stats to CSV (Return: 2.0146% on BTC-USD-15m.csv)
[T00] 🔍 Checking for multi-data test results...
[T00] ⚠️ No multi-data results found at C:\Users\oia89\OneDrive\Desktop\DEX-dev-ai-agents\src\data\rbi_pp_multi\11_11_2025\backtests_package\results\SqueezeBreakout.csv
[T00] 📊 Return: 2.0146% | Target: 50%
[T00] 📈 Need 47.9854% more - Starting optimization
[T00] 🎯 OPTIMIZE #1: 2.0146% → 50%
[T00] Optimize with: openrouter/x-ai/grok-code-fast-1
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 26 queued | 3 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3164 tokens
   💡 Skipping this model for this request...
[T05] ❌ Model error: Model returned None response
[T05] 🔄 Attempt 1 failed, trying fallback...

[T05] 🔄 Attempting fallback models for backtest...
[T05]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: groq (llama-3.3-70b-versatile)
📊 Status: 9 active | 26 queued | 3 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3164 tokens
   💡 Skipping this model for this request...
[T05] ❌ Model error: Model returned None response
[T05] 🔄 Attempt 2 failed, trying fallback...

[T05] 🔄 Attempting fallback models for backtest...
[T05]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T03] 🔧 Debug iteration 1 complete
[T03] 🚀 EXECUTE: Attempt 2/10
[T03] 🚀 Executing: VolumetricBreakout

🔍 Requesting model: groq (llama-3.3-70b-versatile)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3164 tokens
   💡 Skipping this model for this request...
[T05] ❌ Model error: Model returned None response
[T05] ❌ All model attempts failed for backtest
[T05] ❌ FATAL ERROR: 🚨 Could not initialize any model for backtest after 3 attempts!

============================================================
✅ Thread 05 COMPLETED (4 total) - 62.2s
❌ Failed: 🚨 Could not initialize any model for backtest after 3 attempts!
============================================================


🚀 Thread 05 starting: After H&S breakdown, gave a good follow through selling before reversing...
[T05] 🚀 Starting processing
[T05] 🔍 RESEARCH: Starting analysis...

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📊 Status: 9 active | 25 queued | 4 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T08] ✅ Strategy: StochasticBounce
[T08] 📝 Logged processed idea: StochasticBounce
[T08] 📊 BACKTEST: Creating backtest code...
[T08] Using model: groq/llama-3.3-70b-versatile

🔍 Requesting model: groq (llama-3.3-70b-versatile)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T03] ✅ Backtest executed in 6.21s!
[T03] 🎉 BACKTEST SUCCESSFUL!
[T03] 📊 Extracted 8/8 stats
[T03] ⚠️ Return -68.41241% ≤ 1.0% threshold - not saving
[T03] 🔍 Checking for multi-data test results...
[T03] ⚠️ No multi-data results found at C:\Users\oia89\OneDrive\Desktop\DEX-dev-ai-agents\src\data\rbi_pp_multi\11_11_2025\backtests\results\VolumetricBreakout.csv
[T03] 📊 Return: -68.41241% | Target: 50%
[T03] 📈 Need 118.41241% more - Starting optimization
[T03] 🎯 OPTIMIZE #1: -68.41241% → 50%
[T03] Optimize with: openrouter/x-ai/grok-code-fast-1
📊 Status: 9 active | 25 queued | 4 completed | 0 targets hit

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3405 tokens
   💡 Skipping this model for this request...
[T08] ❌ Model error: Model returned None response
[T08] 🔄 Attempt 1 failed, trying fallback...

[T08] 🔄 Attempting fallback models for backtest...
[T08]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: groq (llama-3.3-70b-versatile)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3405 tokens
   💡 Skipping this model for this request...
[T08] ❌ Model error: Model returned None response
[T08] 🔄 Attempt 2 failed, trying fallback...

[T08] 🔄 Attempting fallback models for backtest...
[T08]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
📊 Status: 9 active | 25 queued | 4 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T07] 🔧 Debug iteration 2 complete
[T07] 🚀 EXECUTE: Attempt 3/10
[T07] 🚀 Executing: VolatilityReversion

🔍 Requesting model: groq (llama-3.3-70b-versatile)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T06] 🎯 Optimization 1 complete
[T06] 🚀 Executing: SqueezeRetracement
📊 Status: 9 active | 25 queued | 4 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3405 tokens
   💡 Skipping this model for this request...
[T08] ❌ Model error: Model returned None response
[T08] ❌ All model attempts failed for backtest
[T08] ❌ FATAL ERROR: 🚨 Could not initialize any model for backtest after 3 attempts!

============================================================
✅ Thread 08 COMPLETED (5 total) - 45.6s
❌ Failed: 🚨 Could not initialize any model for backtest after 3 attempts!
============================================================


🚀 Thread 08 starting: LOw ADX signals coiled volatility....
[T08] 🚀 Starting processing
[T08] 🔍 RESEARCH: Starting analysis...

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T07] ✅ Backtest executed in 5.71s!
[T07] 🎉 BACKTEST SUCCESSFUL!
[T07] 📊 Extracted 8/8 stats
[T07] ⚠️ Return -1.1916% ≤ 1.0% threshold - not saving
[T07] 🔍 Checking for multi-data test results...
[T07] ⚠️ No multi-data results found at C:\Users\oia89\OneDrive\Desktop\DEX-dev-ai-agents\src\data\rbi_pp_multi\11_11_2025\backtests\results\VolatilityReversion.csv
[T07] 📊 Return: -1.1916% | Target: 50%
[T07] 📈 Need 51.1916% more - Starting optimization
[T07] 🎯 OPTIMIZE #1: -1.1916% → 50%
[T07] Optimize with: openrouter/x-ai/grok-code-fast-1
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T01] 🔧 Debug iteration 2 complete
[T01] 🚀 EXECUTE: Attempt 3/10
[T01] 🚀 Executing: DivergentReversal

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T04] 🔧 Debug iteration 1 complete
[T04] 🚀 EXECUTE: Attempt 2/10
[T04] 🚀 Executing: VolatilitySwing
📊 Status: 9 active | 24 queued | 5 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T06] ✅ Backtest executed in 6.55s!
[T06] ⚠️ Optimization 1 failed
[T06] 🎯 OPTIMIZE #2: 0.47231% → 50%
[T06] Optimize with: openrouter/x-ai/grok-code-fast-1
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T01] ✅ Backtest executed in 6.32s!
[T01] 🎉 BACKTEST SUCCESSFUL!
[T01] 📊 Extracted 8/8 stats
[T01] ⚠️ Return -0.64008% ≤ 1.0% threshold - not saving
[T01] 🔍 Checking for multi-data test results...
[T01] ⚠️ No multi-data results found at C:\Users\oia89\OneDrive\Desktop\DEX-dev-ai-agents\src\data\rbi_pp_multi\11_11_2025\backtests\results\DivergentReversal.csv
[T01] 📊 Return: -0.64008% | Target: 50%
[T01] 📈 Need 50.64008% more - Starting optimization
[T01] 🎯 OPTIMIZE #1: -0.64008% → 50%
[T01] Optimize with: openrouter/x-ai/grok-code-fast-1

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 24 queued | 5 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T04] ✅ Backtest executed in 6.58s!
[T04] 🎉 BACKTEST SUCCESSFUL!
[T04] 📊 Extracted 8/8 stats
[T04] ⚠️ Return -6.25724% ≤ 1.0% threshold - not saving
[T04] 🔍 Checking for multi-data test results...
[T04] ⚠️ No multi-data results found at C:\Users\oia89\OneDrive\Desktop\DEX-dev-ai-agents\src\data\rbi_pp_multi\11_11_2025\backtests\results\VolatilitySwing.csv
[T04] 📊 Return: -6.25724% | Target: 50%
[T04] 📈 Need 56.25724% more - Starting optimization
[T04] 🎯 OPTIMIZE #1: -6.25724% → 50%
[T04] Optimize with: openrouter/x-ai/grok-code-fast-1
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 24 queued | 5 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T00] 🎯 Optimization 1 complete
[T00] 🚀 Executing: SqueezeBreakout
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 24 queued | 5 completed | 0 targets hit
[T05] ✅ Strategy: AvalancheReversal
[T05] 📝 Logged processed idea: AvalancheReversal
[T05] 📊 BACKTEST: Creating backtest code...
[T05] Using model: groq/llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: groq (llama-3.3-70b-versatile)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 24 queued | 5 completed | 0 targets hit
[T03] 🎯 Optimization 1 complete
[T03] 🚀 Executing: VolumetricBreakout
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3443 tokens
   💡 Skipping this model for this request...
[T05] ❌ Model error: Model returned None response
[T05] 🔄 Attempt 1 failed, trying fallback...

[T05] 🔄 Attempting fallback models for backtest...
[T05]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T03] ❌ Backtest failed: 1
[T03] ⚠️ Optimization 1 failed
[T03] 🎯 OPTIMIZE #2: -68.41241% → 50%
[T03] Optimize with: openrouter/x-ai/grok-code-fast-1
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
[T07] 🎯 Optimization 1 complete
[T07] 🚀 Executing: VolatilityReversion

🔍 Requesting model: groq (llama-3.3-70b-versatile)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 24 queued | 5 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3443 tokens
   💡 Skipping this model for this request...
[T05] ❌ Model error: Model returned None response
[T05] 🔄 Attempt 2 failed, trying fallback...

[T05] 🔄 Attempting fallback models for backtest...
[T05]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: groq (llama-3.3-70b-versatile)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3443 tokens
   💡 Skipping this model for this request...
[T05] ❌ Model error: Model returned None response
[T05] ❌ All model attempts failed for backtest
[T05] ❌ FATAL ERROR: 🚨 Could not initialize any model for backtest after 3 attempts!

============================================================
✅ Thread 05 COMPLETED (6 total) - 50.8s
❌ Failed: 🚨 Could not initialize any model for backtest after 3 attempts!
============================================================


🚀 Thread 05 starting: ADX chop. It's a buildup....
[T05] 🚀 Starting processing
[T05] 🔍 RESEARCH: Starting analysis...
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 23 queued | 6 completed | 0 targets hit

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
[T07] ✅ Backtest executed in 6.11s!
[T07] ⚠️ Optimization 1 failed
[T07] 🎯 OPTIMIZE #2: -1.1916% → 50%
[T07] Optimize with: openrouter/x-ai/grok-code-fast-1
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T00] ✅ Backtest executed in 17.11s!
[T00] ⚠️ Optimization 1 failed
[T00] 🎯 OPTIMIZE #2: 2.0146% → 50%
[T00] Optimize with: openrouter/x-ai/grok-code-fast-1

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T01] 🎯 Optimization 1 complete
[T01] 🚀 Executing: DivergentReversal
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T08] ✅ Strategy: CoiledBreakout
[T08] 📝 Logged processed idea: CoiledBreakout
[T08] 📊 BACKTEST: Creating backtest code...
[T08] Using model: groq/llama-3.3-70b-versatile

🔍 Requesting model: groq (llama-3.3-70b-versatile)
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3108 tokens
   💡 Skipping this model for this request...
[T08] ❌ Model error: Model returned None response
[T08] 🔄 Attempt 1 failed, trying fallback...

[T08] 🔄 Attempting fallback models for backtest...
[T08]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 23 queued | 6 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: groq (llama-3.3-70b-versatile)
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3108 tokens
   💡 Skipping this model for this request...
[T08] ❌ Model error: Model returned None response
[T08] 🔄 Attempt 2 failed, trying fallback...

[T08] 🔄 Attempting fallback models for backtest...
[T08]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T01] ✅ Backtest executed in 6.60s!

🔍 Requesting model: groq (llama-3.3-70b-versatile)[T01] ⚠️ Optimization 1 failed
[T01] 🎯 OPTIMIZE #2: -0.64008% → 50%
[T01] Optimize with: openrouter/x-ai/grok-code-fast-1


🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📊 Status: 9 active | 23 queued | 6 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3108 tokens
   💡 Skipping this model for this request...
[T08] ❌ Model error: Model returned None response
[T08] ❌ All model attempts failed for backtest
[T08] ❌ FATAL ERROR: 🚨 Could not initialize any model for backtest after 3 attempts!

============================================================
✅ Thread 08 COMPLETED (7 total) - 49.3s
❌ Failed: 🚨 Could not initialize any model for backtest after 3 attempts!
============================================================


🚀 Thread 08 starting: ADX model breakout strategy using:...
[T08] 🚀 Starting processing
[T08] 🔍 RESEARCH: Starting analysis...
📊 Status: 9 active | 22 queued | 7 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T06] 🎯 Optimization 2 complete
[T06] 🚀 Executing: SqueezeRetracement
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 22 queued | 7 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T04] 🎯 Optimization 1 complete
[T04] 🚀 Executing: VolatilitySwing
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 22 queued | 7 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T05] ✅ Strategy: ChoppyBuildup
[T05] 📝 Logged processed idea: ChoppyBuildup
[T05] 📊 BACKTEST: Creating backtest code...
[T05] Using model: groq/llama-3.3-70b-versatile

🔍 Requesting model: groq (llama-3.3-70b-versatile)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 2985 tokens
   💡 Skipping this model for this request...
[T05] ❌ Model error: Model returned None response
[T05] 🔄 Attempt 1 failed, trying fallback...

[T05] 🔄 Attempting fallback models for backtest...
[T05]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T03] 🎯 Optimization 2 complete
[T03] 🚀 Executing: VolumetricBreakout
[T07] 🎯 Optimization 2 complete
[T07] 🚀 Executing: VolatilityReversion
📊 Status: 9 active | 22 queued | 7 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: groq (llama-3.3-70b-versatile)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 2985 tokens
   💡 Skipping this model for this request...
[T05] ❌ Model error: Model returned None response
[T05] 🔄 Attempt 2 failed, trying fallback...

[T05] 🔄 Attempting fallback models for backtest...
[T05]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
[T04] ✅ Backtest executed in 8.34s!
[T04] 📊 Extracted 8/8 stats
[T04] 📊 Opt 1: -45.77771% (-39.52%)
[T04] 🎯 OPTIMIZE #2: -6.25724% → 50%
[T04] Optimize with: openrouter/x-ai/grok-code-fast-1

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T03] ❌ Backtest failed: 1
[T03] ⚠️ Optimization 2 failed
[T03] 🎯 OPTIMIZE #3: -68.41241% → 50%
[T03] Optimize with: openrouter/x-ai/grok-code-fast-1

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: groq (llama-3.3-70b-versatile)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 2985 tokens
   💡 Skipping this model for this request...
[T05] ❌ Model error: Model returned None response
[T05] ❌ All model attempts failed for backtest
[T05] ❌ FATAL ERROR: 🚨 Could not initialize any model for backtest after 3 attempts!

============================================================
✅ Thread 05 COMPLETED (8 total) - 34.8s
❌ Failed: 🚨 Could not initialize any model for backtest after 3 attempts!
============================================================


🚀 Thread 05 starting: ADX Volatility = open–low difference...
[T05] 🚀 Starting processing
[T05] 🔍 RESEARCH: Starting analysis...
📊 Status: 9 active | 21 queued | 8 completed | 0 targets hit

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T08] ✅ Strategy: VectorBreakout
[T08] 📝 Logged processed idea: VectorBreakout
[T08] 📊 BACKTEST: Creating backtest code...
[T08] Using model: groq/llama-3.3-70b-versatile

🔍 Requesting model: groq (llama-3.3-70b-versatile)
[T07] ✅ Backtest executed in 6.64s!
[T07] 📊 Extracted 8/8 stats
[T07] 📊 Opt 2: -2.00514% (-0.81%)
[T07] 🎯 OPTIMIZE #3: -1.1916% → 50%
[T07] Optimize with: openrouter/x-ai/grok-code-fast-1
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 2954 tokens
   💡 Skipping this model for this request...
[T08] ❌ Model error: Model returned None response
[T08] 🔄 Attempt 1 failed, trying fallback...

[T08] 🔄 Attempting fallback models for backtest...
[T08]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
[T06] ✅ Backtest executed in 20.65s!
[T06] ⚠️ Optimization 2 failed
[T06] 🎯 OPTIMIZE #3: 0.47231% → 50%
[T06] Optimize with: openrouter/x-ai/grok-code-fast-1
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
[T00] 🎯 Optimization 2 complete
[T00] 🚀 Executing: SqueezeBreakout
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T01] 🎯 Optimization 2 complete
[T01] 🚀 Executing: DivergentReversal

🔍 Requesting model: groq (llama-3.3-70b-versatile)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 2954 tokens
   💡 Skipping this model for this request...
[T08] ❌ Model error: Model returned None response
[T08] 🔄 Attempt 2 failed, trying fallback...

[T08] 🔄 Attempting fallback models for backtest...
[T08]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
📊 Status: 9 active | 21 queued | 8 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: groq (llama-3.3-70b-versatile)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 2954 tokens
   💡 Skipping this model for this request...
[T08] ❌ Model error: Model returned None response
[T08] ❌ All model attempts failed for backtest
[T08] ❌ FATAL ERROR: 🚨 Could not initialize any model for backtest after 3 attempts!

============================================================
✅ Thread 08 COMPLETED (9 total) - 27.9s
❌ Failed: 🚨 Could not initialize any model for backtest after 3 attempts!
============================================================


🚀 Thread 08 starting: ADX Breakout level = low + (3.3 × volatility)...
[T08] 🚀 Starting processing
[T08] 🔍 RESEARCH: Starting analysis...

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 20 queued | 9 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T01] ✅ Backtest executed in 7.48s!
[T01] ⚠️ Optimization 2 failed
[T01] 🎯 OPTIMIZE #3: -0.64008% → 50%
[T01] Optimize with: openrouter/x-ai/grok-code-fast-1
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T00] ✅ Backtest executed in 9.95s!
[T00] ⚠️ Optimization 2 failed
[T00] 🎯 OPTIMIZE #3: 2.0146% → 50%
[T00] Optimize with: openrouter/x-ai/grok-code-fast-1

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 20 queued | 9 completed | 0 targets hit
[T04] 🎯 Optimization 2 complete
[T04] 🚀 Executing: VolatilitySwing
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T04] ❌ Backtest failed: 1
[T04] ⚠️ Optimization 2 failed
[T04] 🎯 OPTIMIZE #3: -6.25724% → 50%
[T04] Optimize with: openrouter/x-ai/grok-code-fast-1

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 20 queued | 9 completed | 0 targets hit
[T03] 🎯 Optimization 3 complete
[T03] 🚀 Executing: VolumetricBreakout
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T07] 🎯 Optimization 3 complete
[T07] 🚀 Executing: VolatilityReversion
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T03] ❌ Backtest failed: 1
[T03] ⚠️ Optimization 3 failed
[T03] 🎯 OPTIMIZE #4: -68.41241% → 50%
[T03] Optimize with: openrouter/x-ai/grok-code-fast-1

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 20 queued | 9 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T07] ✅ Backtest executed in 5.90s!
[T07] ⚠️ Optimization 3 failed
[T07] 🎯 OPTIMIZE #4: -1.1916% → 50%
[T07] Optimize with: openrouter/x-ai/grok-code-fast-1

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 20 queued | 9 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 20 queued | 9 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T05] ✅ Strategy: DirectionalRange
[T05] 📝 Logged processed idea: DirectionalRange
[T05] 📊 BACKTEST: Creating backtest code...
[T05] Using model: groq/llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: groq (llama-3.3-70b-versatile)
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3097 tokens
   💡 Skipping this model for this request...
[T05] ❌ Model error: Model returned None response
[T05] 🔄 Attempt 1 failed, trying fallback...

[T05] 🔄 Attempting fallback models for backtest...
[T05]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 20 queued | 9 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: groq (llama-3.3-70b-versatile)
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3097 tokens
   💡 Skipping this model for this request...
[T05] ❌ Model error: Model returned None response
[T05] 🔄 Attempt 2 failed, trying fallback...

[T05] 🔄 Attempting fallback models for backtest...
[T05]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: groq (llama-3.3-70b-versatile)
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3097 tokens
   💡 Skipping this model for this request...
[T05] ❌ Model error: Model returned None response
[T05] ❌ All model attempts failed for backtest
[T05] ❌ FATAL ERROR: 🚨 Could not initialize any model for backtest after 3 attempts!

============================================================
✅ Thread 05 COMPLETED (10 total) - 43.4s
❌ Failed: 🚨 Could not initialize any model for backtest after 3 attempts!
============================================================


🚀 Thread 05 starting: ADX Stop entries only...
[T05] 🚀 Starting processing
[T05] 🔍 RESEARCH: Starting analysis...
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 19 queued | 10 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T06] 🎯 Optimization 3 complete
[T06] 🚀 Executing: SqueezeRetracement
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T08] ✅ Strategy: ApexBreakout
[T08] 📝 Logged processed idea: ApexBreakout
[T08] 📊 BACKTEST: Creating backtest code...
[T08] Using model: groq/llama-3.3-70b-versatile

🔍 Requesting model: groq (llama-3.3-70b-versatile)
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3332 tokens
   💡 Skipping this model for this request...
[T08] ❌ Model error: Model returned None response
[T08] 🔄 Attempt 1 failed, trying fallback...

[T08] 🔄 Attempting fallback models for backtest...
[T08]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 19 queued | 10 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: groq (llama-3.3-70b-versatile)
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3332 tokens
   💡 Skipping this model for this request...
[T08] ❌ Model error: Model returned None response
[T08] 🔄 Attempt 2 failed, trying fallback...

[T08] 🔄 Attempting fallback models for backtest...
[T08]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
[T07] 🎯 Optimization 4 complete
[T07] 🚀 Executing: VolatilityReversion
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: groq (llama-3.3-70b-versatile)
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3332 tokens
   💡 Skipping this model for this request...
[T08] ❌ Model error: Model returned None response
[T08] ❌ All model attempts failed for backtest
[T08] ❌ FATAL ERROR: 🚨 Could not initialize any model for backtest after 3 attempts!

============================================================
✅ Thread 08 COMPLETED (11 total) - 45.6s
❌ Failed: 🚨 Could not initialize any model for backtest after 3 attempts!
============================================================


🚀 Thread 08 starting: ADX Entry filter: 8am–3pm...
[T06] ✅ Backtest executed in 6.93s!
[T06] 📊 Extracted 7/8 stats
[T06] 📊 Opt 3: 2.21906% (+1.75%)
[T06] ✅ Improved by 1.75%!
[T08] 🚀 Starting processing
[T08] 🔍 RESEARCH: Starting analysis...
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T06] 💾 Saved to working & final! Return: 2.22%
[T06] ✅ Logged stats to CSV (Return: 2.21906% on BTC-USD-15m.csv)
[T06] 🔍 Checking for multi-data test results...
[T06] ⚠️ No multi-data results found at C:\Users\oia89\OneDrive\Desktop\DEX-dev-ai-agents\src\data\rbi_pp_multi\11_11_2025\backtests_optimized\results\SqueezeRetracement.csv
[T06] 🎯 OPTIMIZE #4: 2.21906% → 50%
[T06] Optimize with: openrouter/x-ai/grok-code-fast-1

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
[T04] 🎯 Optimization 3 complete
[T04] 🚀 Executing: VolatilitySwing

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 18 queued | 11 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T00] 🎯 Optimization 3 complete
[T00] 🚀 Executing: SqueezeBreakout
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T07] ✅ Backtest executed in 6.03s!
[T07] ⚠️ Optimization 4 failed
[T07] 🎯 OPTIMIZE #5: -1.1916% → 50%
[T07] Optimize with: openrouter/x-ai/grok-code-fast-1
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T01] 🎯 Optimization 3 complete
[T01] 🚀 Executing: DivergentReversal
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 18 queued | 11 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T04] ✅ Backtest executed in 7.45s!
[T04] 📊 Extracted 8/8 stats
[T04] 📊 Opt 3: -12.0954% (-5.84%)
[T04] 🎯 OPTIMIZE #4: -6.25724% → 50%
[T04] Optimize with: openrouter/x-ai/grok-code-fast-1
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 18 queued | 11 completed | 0 targets hit
[T00] ✅ Backtest executed in 10.00s!
[T00] ⚠️ Optimization 3 failed
[T00] 🎯 OPTIMIZE #4: 2.0146% → 50%
[T00] Optimize with: openrouter/x-ai/grok-code-fast-1
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T01] ✅ Backtest executed in 7.22s!
[T01] 📊 Extracted 8/8 stats
[T01] 📊 Opt 3: -2.32355% (-1.68%)
[T01] 🎯 OPTIMIZE #4: -0.64008% → 50%
[T01] Optimize with: openrouter/x-ai/grok-code-fast-1

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 18 queued | 11 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 18 queued | 11 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T04] 🎯 Optimization 4 complete
[T04] 🚀 Executing: VolatilitySwing
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 18 queued | 11 completed | 0 targets hit
[T05] ✅ Strategy: TrailBreakout
[T05] 📝 Logged processed idea: TrailBreakout
[T05] 📊 BACKTEST: Creating backtest code...
[T05] Using model: groq/llama-3.3-70b-versatile

🔍 Requesting model: groq (llama-3.3-70b-versatile)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T04] ❌ Backtest failed: 1
[T04] ⚠️ Optimization 4 failed
[T04] 🎯 OPTIMIZE #5: -6.25724% → 50%
[T04] Optimize with: openrouter/x-ai/grok-code-fast-1
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3456 tokens
   💡 Skipping this model for this request...
[T05] ❌ Model error: Model returned None response
[T05] 🔄 Attempt 1 failed, trying fallback...

[T05] 🔄 Attempting fallback models for backtest...
[T05]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 18 queued | 11 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: groq (llama-3.3-70b-versatile)
[T08] ✅ Strategy: DirectionalFilter
[T08] 📝 Logged processed idea: DirectionalFilter
[T08] 📊 BACKTEST: Creating backtest code...
[T08] Using model: groq/llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3456 tokens
   💡 Skipping this model for this request...
[T05] ❌ Model error: Model returned None response
[T05] 🔄 Attempt 2 failed, trying fallback...

[T05] 🔄 Attempting fallback models for backtest...
[T05]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile

🔍 Requesting model: groq (llama-3.3-70b-versatile)
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3531 tokens
   💡 Skipping this model for this request...
[T08] ❌ Model error: Model returned None response
[T08] 🔄 Attempt 1 failed, trying fallback...

[T08] 🔄 Attempting fallback models for backtest...
[T08]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: groq (llama-3.3-70b-versatile)
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3456 tokens
   💡 Skipping this model for this request...
[T05] ❌ Model error: Model returned None response
[T05] ❌ All model attempts failed for backtest
[T05] ❌ FATAL ERROR: 🚨 Could not initialize any model for backtest after 3 attempts!

============================================================
✅ Thread 05 COMPLETED (12 total) - 46.8s
❌ Failed: 🚨 Could not initialize any model for backtest after 3 attempts!
============================================================


🚀 Thread 05 starting: ADX Exit: when ADX > 40 or after time limit...
[T05] 🚀 Starting processing
[T05] 🔍 RESEARCH: Starting analysis...
📊 Status: 9 active | 17 queued | 12 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: groq (llama-3.3-70b-versatile)
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3531 tokens
   💡 Skipping this model for this request...
[T08] ❌ Model error: Model returned None response
[T08] 🔄 Attempt 2 failed, trying fallback...

[T08] 🔄 Attempting fallback models for backtest...
[T08]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: groq (llama-3.3-70b-versatile)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3531 tokens
   💡 Skipping this model for this request...
[T08] ❌ Model error: Model returned None response
[T08] ❌ All model attempts failed for backtest
[T08] ❌ FATAL ERROR: 🚨 Could not initialize any model for backtest after 3 attempts!

============================================================
✅ Thread 08 COMPLETED (13 total) - 39.9s
❌ Failed: 🚨 Could not initialize any model for backtest after 3 attempts!
============================================================


🚀 Thread 08 starting: ADX Calibration...
[T08] 🚀 Starting processing
[T08] 🔍 RESEARCH: Starting analysis...

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
[T03] 🎯 Optimization 4 complete
[T03] 🚀 Executing: VolumetricBreakout
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 16 queued | 13 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T03] ❌ Backtest failed: 1
[T03] ⚠️ Optimization 4 failed
[T03] 🎯 OPTIMIZE #5: -68.41241% → 50%
[T03] Optimize with: openrouter/x-ai/grok-code-fast-1

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T06] 🎯 Optimization 4 complete
[T06] 🚀 Executing: SqueezeRetracement
[T07] 🎯 Optimization 5 complete
[T07] 🚀 Executing: VolatilityReversion
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T00] 🎯 Optimization 4 complete
[T00] 🚀 Executing: SqueezeBreakout
📊 Status: 9 active | 16 queued | 13 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T06] ✅ Backtest executed in 2.83s!
[T06] 📊 Extracted 0/8 stats
[T06] 🎯 OPTIMIZE #5: 2.21906% → 50%
[T06] Optimize with: openrouter/x-ai/grok-code-fast-1

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 16 queued | 13 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T07] ✅ Backtest executed in 7.41s!
[T07] 📊 Extracted 8/8 stats
[T07] 📊 Opt 5: -0.28332% (+0.91%)
[T07] ✅ Improved by 0.91%!
[T07] ⚠️ Return -0.28332% ≤ 1.0% threshold - not saving
[T07] 🔍 Checking for multi-data test results...
[T07] ⚠️ No multi-data results found at C:\Users\oia89\OneDrive\Desktop\DEX-dev-ai-agents\src\data\rbi_pp_multi\11_11_2025\backtests_optimized\results\VolatilityReversion.csv
[T07] 🎯 OPTIMIZE #6: -0.28332% → 50%
[T07] Optimize with: openrouter/x-ai/grok-code-fast-1
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T04] 🎯 Optimization 5 complete
[T04] 🚀 Executing: VolatilitySwing
📊 Status: 9 active | 16 queued | 13 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T00] ✅ Backtest executed in 10.61s!
[T00] ⚠️ Optimization 4 failed
[T00] 🎯 OPTIMIZE #5: 2.0146% → 50%
[T00] Optimize with: openrouter/x-ai/grok-code-fast-1

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T04] ❌ Backtest failed: 1
[T04] ⚠️ Optimization 5 failed
[T04] 🎯 OPTIMIZE #6: -6.25724% → 50%
[T04] Optimize with: openrouter/x-ai/grok-code-fast-1
[T01] 🎯 Optimization 4 complete
[T01] 🚀 Executing: DivergentReversal

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 16 queued | 13 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T03] 🎯 Optimization 5 complete
[T03] 🚀 Executing: VolumetricBreakout
📊 Status: 9 active | 16 queued | 13 completed | 0 targets hit
[T01] ✅ Backtest executed in 6.39s!
[T01] ⚠️ Optimization 4 failed
[T01] 🎯 OPTIMIZE #5: -0.64008% → 50%
[T01] Optimize with: openrouter/x-ai/grok-code-fast-1
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T03] ❌ Backtest failed: 1
[T03] ⚠️ Optimization 5 failed
[T03] 🎯 OPTIMIZE #6: -68.41241% → 50%
[T03] Optimize with: openrouter/x-ai/grok-code-fast-1

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 16 queued | 13 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 16 queued | 13 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T05] ✅ Strategy: TimedThreshold
[T05] 📝 Logged processed idea: TimedThreshold
[T05] 📊 BACKTEST: Creating backtest code...
[T05] Using model: groq/llama-3.3-70b-versatile

🔍 Requesting model: groq (llama-3.3-70b-versatile)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3413 tokens
   💡 Skipping this model for this request...
[T05] ❌ Model error: Model returned None response
[T05] 🔄 Attempt 1 failed, trying fallback...

[T05] 🔄 Attempting fallback models for backtest...
[T05]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 16 queued | 13 completed | 0 targets hit

🔍 Requesting model: groq (llama-3.3-70b-versatile)
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3413 tokens
   💡 Skipping this model for this request...
[T05] ❌ Model error: Model returned None response
[T05] 🔄 Attempt 2 failed, trying fallback...

[T05] 🔄 Attempting fallback models for backtest...
[T05]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: groq (llama-3.3-70b-versatile)
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3413 tokens
   💡 Skipping this model for this request...
[T05] ❌ Model error: Model returned None response
[T05] ❌ All model attempts failed for backtest
[T05] ❌ FATAL ERROR: 🚨 Could not initialize any model for backtest after 3 attempts!

============================================================
✅ Thread 05 COMPLETED (14 total) - 48.8s
❌ Failed: 🚨 Could not initialize any model for backtest after 3 attempts!
============================================================


🚀 Thread 05 starting: ADX multiple markets to find robust parameters....
[T05] 🚀 Starting processing
[T05] 🔍 RESEARCH: Starting analysis...
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📊 Status: 9 active | 15 queued | 14 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T07] 🎯 Optimization 6 complete
[T07] 🚀 Executing: VolatilityReversion
[T06] 🎯 Optimization 5 complete
[T06] 🚀 Executing: SqueezeRetracement
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T06] ✅ Backtest executed in 3.30s!
[T06] 📊 Extracted 0/8 stats
[T06] 🎯 OPTIMIZE #6: 2.21906% → 50%
[T06] Optimize with: openrouter/x-ai/grok-code-fast-1
📊 Status: 9 active | 15 queued | 14 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T08] ✅ Strategy: CalibrationDirectional
[T08] 📝 Logged processed idea: CalibrationDirectional
[T08] 📊 BACKTEST: Creating backtest code...
[T08] Using model: groq/llama-3.3-70b-versatile

🔍 Requesting model: groq (llama-3.3-70b-versatile)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3069 tokens
   💡 Skipping this model for this request...
[T08] ❌ Model error: Model returned None response
[T08] 🔄 Attempt 1 failed, trying fallback...

[T08] 🔄 Attempting fallback models for backtest...
[T08]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T01] 🎯 Optimization 5 complete
[T01] 🚀 Executing: DivergentReversal
[T07] ✅ Backtest executed in 8.11s!
[T07] ⚠️ Optimization 6 failed
[T07] 🎯 OPTIMIZE #7: -0.28332% → 50%
[T07] Optimize with: openrouter/x-ai/grok-code-fast-1

🔍 Requesting model: groq (llama-3.3-70b-versatile)
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3069 tokens
   💡 Skipping this model for this request...
[T08] ❌ Model error: Model returned None response
[T08] 🔄 Attempt 2 failed, trying fallback...

[T08] 🔄 Attempting fallback models for backtest...
[T08]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
📊 Status: 9 active | 15 queued | 14 completed | 0 targets hit

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T03] 🎯 Optimization 6 complete
[T03] 🚀 Executing: VolumetricBreakout
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: groq (llama-3.3-70b-versatile)
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3069 tokens
   💡 Skipping this model for this request...
[T08] ❌ Model error: Model returned None response
[T08] ❌ All model attempts failed for backtest
[T08] ❌ FATAL ERROR: 🚨 Could not initialize any model for backtest after 3 attempts!

============================================================
✅ Thread 08 COMPLETED (15 total) - 59.4s
❌ Failed: 🚨 Could not initialize any model for backtest after 3 attempts!
============================================================


🚀 Thread 08 starting: ADX overfitting to one instrument....
[T08] 🚀 Starting processing
[T08] 🔍 RESEARCH: Starting analysis...

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T03] ❌ Backtest failed: 1
[T03] ⚠️ Optimization 6 failed
[T03] 🎯 OPTIMIZE #7: -68.41241% → 50%
[T03] Optimize with: openrouter/x-ai/grok-code-fast-1
📊 Status: 9 active | 14 queued | 15 completed | 0 targets hit

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T01] ✅ Backtest executed in 7.34s!
[T01] ⚠️ Optimization 5 failed
[T01] 🎯 OPTIMIZE #6: -0.64008% → 50%
[T01] Optimize with: openrouter/x-ai/grok-code-fast-1
[T04] 🎯 Optimization 6 complete
[T04] 🚀 Executing: VolatilitySwing

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 14 queued | 15 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T00] 🎯 Optimization 5 complete
[T00] 🚀 Executing: SqueezeBreakout
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T06] 🎯 Optimization 6 complete
[T06] 🚀 Executing: SqueezeRetracement
[T06] ❌ Backtest failed: 1
[T06] ⚠️ Optimization 6 failed
[T06] 🎯 OPTIMIZE #7: 2.21906% → 50%
[T06] Optimize with: openrouter/x-ai/grok-code-fast-1
[T04] ✅ Backtest executed in 7.69s!
[T04] ⚠️ Optimization 6 failed
[T04] 🎯 OPTIMIZE #7: -6.25724% → 50%
[T04] Optimize with: openrouter/x-ai/grok-code-fast-1
📊 Status: 9 active | 14 queued | 15 completed | 0 targets hit

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T05] ✅ Strategy: EnsembleDirectional
[T05] 📝 Logged processed idea: EnsembleDirectional
[T05] 📊 BACKTEST: Creating backtest code...
[T05] Using model: groq/llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: groq (llama-3.3-70b-versatile)
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3254 tokens
   💡 Skipping this model for this request...
[T05] ❌ Model error: Model returned None response
[T05] 🔄 Attempt 1 failed, trying fallback...

[T05] 🔄 Attempting fallback models for backtest...
[T05]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 14 queued | 15 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: groq (llama-3.3-70b-versatile)
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3254 tokens
   💡 Skipping this model for this request...
[T05] ❌ Model error: Model returned None response
[T05] 🔄 Attempt 2 failed, trying fallback...

[T05] 🔄 Attempting fallback models for backtest...
[T05]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T00] ✅ Backtest executed in 8.82s!
[T00] ⚠️ Optimization 5 failed
[T00] 🎯 OPTIMIZE #6: 2.0146% → 50%
[T00] Optimize with: openrouter/x-ai/grok-code-fast-1
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: groq (llama-3.3-70b-versatile)
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3254 tokens
   💡 Skipping this model for this request...
[T05] ❌ Model error: Model returned None response
[T05] ❌ All model attempts failed for backtest
[T05] ❌ FATAL ERROR: 🚨 Could not initialize any model for backtest after 3 attempts!

============================================================
✅ Thread 05 COMPLETED (16 total) - 35.8s
❌ Failed: 🚨 Could not initialize any model for backtest after 3 attempts!
============================================================


🚀 Thread 05 starting: recent and current ADX strength....
[T05] 🚀 Starting processing
[T05] 🔍 RESEARCH: Starting analysis...
[T07] 🎯 Optimization 7 complete
[T07] 🚀 Executing: VolatilityReversion

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 13 queued | 16 completed | 0 targets hit
[T01] 🎯 Optimization 6 complete
[T01] 🚀 Executing: DivergentReversal
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T07] ❌ Backtest failed: 1
[T07] ⚠️ Optimization 7 failed
[T07] 🎯 OPTIMIZE #8: -0.28332% → 50%
[T07] Optimize with: openrouter/x-ai/grok-code-fast-1
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 13 queued | 16 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 13 queued | 16 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T01] ✅ Backtest executed in 10.62s!
[T01] ⚠️ Optimization 6 failed
[T01] 🎯 OPTIMIZE #7: -0.64008% → 50%
[T01] Optimize with: openrouter/x-ai/grok-code-fast-1
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📊 Status: 9 active | 13 queued | 16 completed | 0 targets hit
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T04] 🎯 Optimization 7 complete
[T04] 🚀 Executing: VolatilitySwing
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T05] ✅ Strategy: AdaptiveDirectional
[T05] 📝 Logged processed idea: AdaptiveDirectional
[T05] 📊 BACKTEST: Creating backtest code...
[T05] Using model: groq/llama-3.3-70b-versatile

🔍 Requesting model: groq (llama-3.3-70b-versatile)
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3084 tokens
   💡 Skipping this model for this request...
[T05] ❌ Model error: Model returned None response
[T05] 🔄 Attempt 1 failed, trying fallback...

[T05] 🔄 Attempting fallback models for backtest...
[T05]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
[T06] 🎯 Optimization 7 complete
[T06] 🚀 Executing: SqueezeRetracement
[T08] ✅ Strategy: RobustDirectional
[T08] 📝 Logged processed idea: RobustDirectional
[T08] 📊 BACKTEST: Creating backtest code...
[T08] Using model: groq/llama-3.3-70b-versatile
📊 Status: 9 active | 13 queued | 16 completed | 0 targets hit

🔍 Requesting model: groq (llama-3.3-70b-versatile)
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3470 tokens
   💡 Skipping this model for this request...
[T08] ❌ Model error: Model returned None response
[T08] 🔄 Attempt 1 failed, trying fallback...

[T08] 🔄 Attempting fallback models for backtest...
[T08]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: groq (llama-3.3-70b-versatile)
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3084 tokens
   💡 Skipping this model for this request...
[T05] ❌ Model error: Model returned None response
[T05] 🔄 Attempt 2 failed, trying fallback...

[T05] 🔄 Attempting fallback models for backtest...
[T05]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
[T06] ✅ Backtest executed in 2.56s!
[T06] 📊 Extracted 0/8 stats
[T06] 🎯 OPTIMIZE #8: 2.21906% → 50%
[T06] Optimize with: openrouter/x-ai/grok-code-fast-1
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)

🔍 Requesting model: groq (llama-3.3-70b-versatile)
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3470 tokens
   💡 Skipping this model for this request...
[T08] ❌ Model error: Model returned None response
[T08] 🔄 Attempt 2 failed, trying fallback...

[T08] 🔄 Attempting fallback models for backtest...
[T08]   ✓ Fallback 1/3: groq - llama-3.3-70b-versatile
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: groq (llama-3.3-70b-versatile)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3084 tokens
   💡 Skipping this model for this request...
[T05] ❌ Model error: Model returned None response
[T05] ❌ All model attempts failed for backtest
[T05] ❌ FATAL ERROR: 🚨 Could not initialize any model for backtest after 3 attempts!

============================================================
✅ Thread 05 COMPLETED (17 total) - 25.3s
❌ Failed: 🚨 Could not initialize any model for backtest after 3 attempts!
============================================================


🚀 Thread 05 starting: ATR-based, trailing stops, volatility brackets...
[T05] 🚀 Starting processing
[T05] 🔍 RESEARCH: Starting analysis...
[T02] ❌ FATAL ERROR: Command '['C:\\Python313\\python.exe', 'C:\\Users\\oia89\\OneDrive\\Desktop\\DEX-dev-ai-agents\\src\\data\\rbi_pp_multi\\11_11_2025\\backtests\\T02_VolatilityReversal_DEBUG_v1.py']' timed out after 300 seconds

============================================================
✅ Thread 02 COMPLETED (18 total) - 409.9s
❌ Failed: Command '['C:\\Python313\\python.exe', 'C:\\Users\\oia89\\OneDrive\\Desktop\\DEX-dev-ai-agents\\src\\data\\rbi_pp_multi\\11_11_2025\\backtests\\T02_VolatilityReversal_DEBUG_v1.py']' timed out after 300 seconds
============================================================


🚀 Thread 02 starting: MCSO>=50...
[T02] 🚀 Starting processing
[T02] 🔍 RESEARCH: Starting analysis...
📊 Status: 9 active | 11 queued | 18 completed | 0 targets hit

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
[T04] ✅ Backtest executed in 7.72s!

🔍 Requesting model: groq (llama-3.3-70b-versatile)
[T04] ⚠️ Optimization 7 failed
[T04] 🎯 OPTIMIZE #8: -6.25724% → 50%
[T04] Optimize with: openrouter/x-ai/grok-code-fast-1
⚠️  Groq rate limit exceeded (request too large)
   Model: llama-3.3-70b-versatile
   Limit: 100000 tokens | Requested: 3470 tokens
   💡 Skipping this model for this request...
[T08] ❌ Model error: Model returned None response
[T08] ❌ All model attempts failed for backtest
[T08] ❌ FATAL ERROR: 🚨 Could not initialize any model for backtest after 3 attempts!

============================================================
✅ Thread 08 COMPLETED (19 total) - 48.8s
❌ Failed: 🚨 Could not initialize any model for backtest after 3 attempts!
============================================================


🚀 Thread 08 starting: Triple Exponential MA (distance from close)....
[T08] 🚀 Starting processing
[T08] 🔍 RESEARCH: Starting analysis...
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)

🔍 Requesting model: openrouter (x-ai/grok-code-fast-1)
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt
📁 Found 12 pre-researched strategies
💡 Found 26 raw ideas in ideas.txt


🛑 Shutting down gracefully...

============================================================
📊 FINAL STATS
============================================================
✅ Successful: 0
🎯 Targets hit: 0
❌ Failed: 19
📊 Total completed: 19
============================================================

(venv) PS C:\Users\oia89\OneDrive\Desktop\DEX-dev-ai-agents>