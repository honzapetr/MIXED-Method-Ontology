# 3. Local models through an OpenAI-compatible gateway

- Status: accepted (owner: local first), backends open for testing

## Context

The owner runs models on a homelab: a LiteLLM gateway in front of vLLM slots on a GPU server and Ollama on an
always-on server (repository `honzapetr/aiops-homelab`). Which models do OCR and analysis is not decided; variants
will be tested. Cloud models are allowed but not the default.

## Decision

Model calls go through an OpenAI-compatible `chat/completions` client configured from `.env`
(`MMO_OPENAI_BASE_URL`, key, model). The same client works with the gateway, Ollama and vLLM, and Claude can be
added behind the gateway. Tesseract is the local non-LLM OCR baseline. Every result stores backend, model and prompt
version, and results of variants are kept side by side.

## Consequences

No provider SDKs in the core; switching a model is a setting. Homelab-only addresses never enter the repository.
The GPU server may need to be started (fabricd) before long runs; a lease client is planned.
