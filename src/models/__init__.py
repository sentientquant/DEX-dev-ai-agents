#!/usr/bin/env python3
"""
Moon Dev's AI Models Package

Provides unified interface to multiple AI providers:
- Claude (Anthropic)
- Groq (Fast inference)
- Gemini (Google)
- DeepSeek (Reasoning)
- Ollama (Local)
- XAI (Grok)
- OpenRouter (200+ models)
"""

from src.models.model_factory import ModelFactory, model_factory

__all__ = ['ModelFactory', 'model_factory']
