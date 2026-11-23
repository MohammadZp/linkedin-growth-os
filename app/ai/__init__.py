"""Optional LLM integration.

The app is fully usable without an LLM. Providers are selected via ``AI_PROVIDER``
and constructed lazily; no key is hardcoded and no prompt is sent without the user
requesting it.
"""
