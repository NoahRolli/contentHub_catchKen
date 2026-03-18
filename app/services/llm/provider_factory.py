# app/services/llm/provider_factory.py
# ============================================================
# Factory Pattern: Erstellt den richtigen LLM-Provider
# basierend auf der Konfiguration in .env.
#
# Warum Factory?
# Der Rest der App ruft nur get_llm_provider() auf und bekommt
# einen Provider zurück — ob das Ollama oder OpenAI ist, ist egal.
# Zum Wechseln reicht es, LLM_PROVIDER in .env zu ändern.
# ============================================================

from functools import lru_cache  # Cacht das Ergebnis → Provider wird nur 1x erstellt

from app.services.llm.base_provider import BaseLLMProvider
from app.services.llm.ollama_provider import OllamaProvider


# lru_cache sorgt dafür dass die Funktion nur beim ersten Aufruf
# ausgeführt wird. Danach wird immer die gleiche Provider-Instanz
# zurückgegeben. Das spart Ressourcen und vermeidet doppelte Connections.
@lru_cache(maxsize=1)
def get_llm_provider() -> BaseLLMProvider:
    """
    Erstellt und cached den LLM-Provider basierend auf der App-Konfiguration.

    Liest LLM_PROVIDER aus der Config (.env):
        - "ollama" → OllamaProvider (lokal, kostenlos, braucht Ollama Server)
        - "openai" → OpenAIProvider (Cloud, kostenpflichtig, zuverlässiger)

    Returns:
        Eine Instanz von BaseLLMProvider (entweder Ollama oder OpenAI)

    Raises:
        ValueError: Wenn ein unbekannter Provider in .env konfiguriert ist
    """
    # Import hier statt oben → vermeidet zirkuläre Imports
    # (config importiert evtl. etwas das wiederum llm importiert)
    from app.core.config import get_settings
    settings = get_settings()

    # Provider-Name aus .env lesen (default: "ollama")
    provider_name = getattr(settings, "LLM_PROVIDER", "ollama").lower()

    if provider_name == "ollama":
        # Ollama-spezifische Settings aus .env lesen
        return OllamaProvider(
            base_url=getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434"),
            model=getattr(settings, "OLLAMA_MODEL", "llama3.2"),
            timeout=float(getattr(settings, "OLLAMA_TIMEOUT", 120.0))
        )

    elif provider_name == "openai":
        # OpenAI Provider wird in Phase 3b implementiert
        # Für jetzt: ImportError mit hilfreicher Nachricht
        try:
            from app.services.llm.openai_provider import OpenAIProvider
            return OpenAIProvider(
                api_key=getattr(settings, "OPENAI_API_KEY", ""),
                model=getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
            )
        except ImportError:
            raise NotImplementedError(
                "OpenAI Provider ist noch nicht implementiert. "
                "Setze LLM_PROVIDER=ollama in .env oder warte auf Phase 3b."
            )

    else:
        # Unbekannter Provider → klare Fehlermeldung
        raise ValueError(
            f"Unbekannter LLM Provider: '{provider_name}'. "
            f"Erlaubte Werte: 'ollama', 'openai'. "
            f"Prüfe LLM_PROVIDER in deiner .env Datei."
        )


def reset_provider_cache():
    """
    Leert den Provider-Cache. Nötig wenn sich die Config zur Laufzeit ändert
    (z.B. in Tests oder wenn man den Provider dynamisch wechseln will).
    """
    get_llm_provider.cache_clear()