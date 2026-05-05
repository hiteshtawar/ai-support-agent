"""Configuration for the Sample Company support agent."""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """All tuneable settings for the support agent in one place.

    Attributes:
        model: The Ollama model tag to use for inference.
        max_tokens: Upper bound on tokens in a single model response.
        temperature: Sampling temperature — lower is more deterministic.
        system_prompt: The instruction block prepended to every conversation.
    """

    model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "llama3.2"))
    max_tokens: int = 1024
    temperature: float = 0.2
    system_prompt: str = (
        "You are a helpful support agent for Sample App, the SaaS product built by Sample Company. "
        "Your job is to answer user questions accurately and concisely.\n\n"
        "Rules:\n"
        "1. Always call search_faq first when a user describes a problem or asks a how-to question.\n"
        "2. If search_faq returns a result, answer using that information — do not invent details.\n"
        "3. If search_faq finds nothing, acknowledge that and offer to create a support ticket.\n"
        "4. Before calling create_ticket, ask the user for their email address if you don't have it.\n"
        "5. Be friendly but brief. Bullet points are fine; walls of text are not.\n"
        "6. Never claim features or policies that aren't in the FAQ."
    )


# Module-level default so callers can do `from config import config` directly.
config = Config()
