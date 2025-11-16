"""A unified interface for querying Large Language Models (LLMs) across multiple providers."""

from .llm import LLM
from .model_router import ModelRouter

__version__ = "0.1.1"
__all__ = ["LLM", "ModelRouter"]

