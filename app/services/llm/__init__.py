# app/services/llm/__init__.py
# ============================================================
# Package-Exports für den LLM-Service.
# Ermöglicht saubere Imports im Rest der App:
#
#   from app.services.llm import get_llm_provider
#   from app.services.llm import OllamaProvider
#
# Statt:
#   from app.services.llm.provider_factory import get_llm_provider
#   from app.services.llm.ollama_provider import OllamaProvider
# ============================================================

from app.services.llm.provider_factory import get_llm_provider, reset_provider_cache
from app.services.llm.base_provider import BaseLLMProvider
from app.services.llm.ollama_provider import OllamaProvider
from app.services.llm.training_data import (
    get_training_examples,
    has_training_data,
    get_training_data_stats,
)

# __all__ definiert was bei "from app.services.llm import *" exportiert wird
# (Best Practice: explizit sein statt alles zu exportieren)
__all__ = [
    "get_llm_provider",
    "reset_provider_cache",
    "BaseLLMProvider",
    "OllamaProvider",
    "get_training_examples",
    "has_training_data",
    "get_training_data_stats",
]