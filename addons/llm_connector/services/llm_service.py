import logging
import requests
from odoo import models

_logger = logging.getLogger(__name__)


class LlmService(models.AbstractModel):
    """Unified LLM access layer with completion and embedding APIs."""

    _name = "llm.connector.service"
    _description = "LLM Connector Service"

    def _get_default_backend(self):
        backend = self.env["llm.backend"].search([("is_default", "=", True)], limit=1)
        if not backend:
            backend = self.env["llm.backend"].search([], limit=1)
        if not backend:
            raise ValueError("No llm.backend configured")
        return backend

    def embed_text(self, text, backend=None):
        backend = backend or self._get_default_backend()
        payload = self._build_embedding_payload(backend, text)
        response = self._request_backend(backend, payload, mode="embedding")
        return self._extract_embedding(backend, response)

    def complete(self, prompt, backend=None, temperature=0.0):
        backend = backend or self._get_default_backend()
        payload = self._build_completion_payload(backend, prompt, temperature)
        response = self._request_backend(backend, payload, mode="completion")
        return self._extract_completion(backend, response)

    def _request_backend(self, backend, payload, mode):
        headers = {"Content-Type": "application/json"}
        options = backend.get_options()
        timeout = options.get("timeout", 60)
        if backend.provider in ("openai", "gemini") and backend.api_key:
            if backend.provider == "openai":
                headers["Authorization"] = f"Bearer {backend.api_key}"
            else:
                headers["x-goog-api-key"] = backend.api_key

        endpoint = self._resolve_endpoint(backend, mode)
        _logger.debug("Calling %s backend %s at %s", mode, backend.provider, endpoint)
        response = requests.post(endpoint, json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()

    def _resolve_endpoint(self, backend, mode):
        if backend.provider == "openai":
            base = backend.endpoint or "https://api.openai.com/v1"
            return f"{base}/embeddings" if mode == "embedding" else f"{base}/chat/completions"
        if backend.provider == "gemini":
            base = backend.endpoint or "https://generativelanguage.googleapis.com/v1beta"
            suffix = ":embedContent" if mode == "embedding" else ":generateContent"
            model = backend.embedding_model if mode == "embedding" else backend.completion_model
            return f"{base}/models/{model}{suffix}"
        base = backend.endpoint or "http://localhost:11434/api"
        return f"{base}/embeddings" if mode == "embedding" else f"{base}/generate"

    def _build_embedding_payload(self, backend, text):
        if backend.provider == "openai":
            return {"model": backend.embedding_model, "input": text}
        if backend.provider == "gemini":
            return {"content": {"parts": [{"text": text}]}}
        return {"model": backend.embedding_model, "prompt": text}

    def _build_completion_payload(self, backend, prompt, temperature):
        if backend.provider == "openai":
            return {
                "model": backend.completion_model,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}],
            }
        if backend.provider == "gemini":
            return {"contents": [{"parts": [{"text": prompt}]}]}
        return {"model": backend.completion_model, "prompt": prompt, "temperature": temperature}

    def _extract_embedding(self, backend, response):
        if backend.provider == "openai":
            return response["data"][0]["embedding"]
        if backend.provider == "gemini":
            return response["embedding"]["values"]
        return response["embedding"]

    def _extract_completion(self, backend, response):
        if backend.provider == "openai":
            return response["choices"][0]["message"]["content"]
        if backend.provider == "gemini":
            return response["candidates"][0]["content"]["parts"][0]["text"]
        return response.get("response", "")
