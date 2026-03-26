"""Direct Anthropic API provider — much faster than CLI for real-time use."""

import base64
import logging
import os

from ai.provider import AIProvider

logger = logging.getLogger(__name__)


class AnthropicProvider(AIProvider):
    """Calls Claude API directly via the anthropic Python SDK. ~3x faster than CLI."""

    def __init__(self, model: str = "claude-sonnet-4-20250514", api_key: str | None = None):
        self.model = model
        self._client = None
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")

    def _get_client(self):
        if self._client is None:
            if not self._api_key:
                raise RuntimeError(
                    "ANTHROPIC_API_KEY not set. Either:\n"
                    "  1. export ANTHROPIC_API_KEY=sk-ant-...\n"
                    "  2. Add api_key to config.toml under [ai]\n"
                    "  3. Set default_provider = 'claude-cli' to use the slower CLI method"
                )
            import anthropic
            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    def get_response(self, prompt: str, context: str = "") -> str:
        client = self._get_client()
        messages = [{"role": "user", "content": prompt}]
        try:
            resp = client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=context if context else "You are a helpful meeting assistant.",
                messages=messages,
            )
            return resp.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return f"Error: {e}"

    def analyze_image(self, image_path: str, prompt: str, context: str = "") -> str:
        """Send screenshot directly to Claude Vision API — fast."""
        client = self._get_client()

        # Read and base64 encode the image
        with open(image_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")

        messages = [{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image_data,
                    },
                },
                {
                    "type": "text",
                    "text": prompt,
                },
            ],
        }]

        try:
            resp = client.messages.create(
                model=self.model,
                max_tokens=1500,
                system=context if context else "You are a helpful meeting assistant.",
                messages=messages,
            )
            return resp.content[0].text
        except Exception as e:
            logger.error(f"Anthropic Vision API error: {e}")
            return f"Error: {e}"

    def stream_response(self, prompt: str, context: str = "", callback=None) -> str:
        """Stream response token-by-token."""
        client = self._get_client()
        messages = [{"role": "user", "content": prompt}]
        full = []

        try:
            with client.messages.stream(
                model=self.model,
                max_tokens=1500,
                system=context if context else "You are a helpful meeting assistant.",
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    full.append(text)
                    if callback:
                        callback(text)
            return "".join(full)
        except Exception as e:
            logger.error(f"Anthropic stream error: {e}")
            return f"Error: {e}"
