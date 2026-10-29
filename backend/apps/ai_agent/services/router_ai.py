"""
RouterAI API client — OpenAI-compatible interface.

Supports LLM chat, embeddings, TTS, and STT.
"""
import logging
import base64
import io

from openai import OpenAI
from django.conf import settings

logger = logging.getLogger(__name__)

# MIME type per ROUTERAI_TTS_FORMAT, so views do not hardcode audio/mpeg.
_TTS_CONTENT_TYPES = {
    'mp3': 'audio/mpeg',
    'wav': 'audio/wav',
    'opus': 'audio/ogg',
    'flac': 'audio/flac',
    'pcm': 'audio/L16;rate=24000;channels=1',
}


def tts_content_type() -> str:
    """MIME type matching the configured TTS ``response_format``."""
    fmt = (getattr(settings, 'ROUTERAI_TTS_FORMAT', 'mp3') or 'mp3').lower()
    return _TTS_CONTENT_TYPES.get(fmt, f'audio/{fmt}')


class RouterAIClient:
    """
    Client for RouterAI API (OpenAI-compatible).
    
    Usage:
        client = RouterAIClient()
        response = client.chat_completion([{"role": "user", "content": "Hello"}])
        embeddings = client.embeddings(["text to embed"])
        audio = client.tts("Text to speak")
        text = client.stt(audio_file)
    """

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.ROUTERAI_API_KEY,
            base_url=settings.ROUTERAI_BASE_URL,
        )

    def chat_completion(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> tuple[str, int]:
        """
        Generate a chat completion.

        Returns:
            (response_text, tokens_used)
        """
        model = model or settings.ROUTERAI_LLM_MODEL

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
            text = response.choices[0].message.content or ''
            tokens = response.usage.total_tokens if response.usage else 0
            return text, tokens

        except Exception as e:
            logger.error(f"RouterAI chat completion error: {e}")
            raise

    def chat_completion_with_tools(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ):
        """
        Generate a chat completion with function calling support.

        Returns:
            The full response object (may contain tool_calls)
        """
        model = model or settings.ROUTERAI_LLM_MODEL

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
            )
            return response

        except Exception as e:
            logger.error(f"RouterAI tool calling error: {e}")
            raise

    def embeddings(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        """
        Generate embeddings for a list of texts.

        Returns:
            List of embedding vectors
        """
        model = model or settings.ROUTERAI_EMBEDDINGS_MODEL

        try:
            response = self.client.embeddings.create(
                model=model,
                input=texts,
            )
            return [item.embedding for item in response.data]

        except Exception as e:
            logger.error(f"RouterAI embeddings error: {e}")
            raise

    def tts(
        self,
        text: str,
        model: str | None = None,
        voice: str | None = None,
        response_format: str | None = None,
    ) -> bytes:
        """
        Generate text-to-speech audio.

        ``response_format`` must be requested explicitly: without it the router
        falls back to raw PCM (which the browser cannot play from a Blob URL),
        and MiniMax rejects the call outright.

        Returns:
            Audio bytes in ``response_format`` (mp3 by default)
        """
        model = model or settings.ROUTERAI_TTS_MODEL
        voice = voice or settings.ROUTERAI_TTS_VOICE
        response_format = response_format or settings.ROUTERAI_TTS_FORMAT

        try:
            response = self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                response_format=response_format,
            )
            return response.content

        except Exception as e:
            logger.error(f"RouterAI TTS error: {e}")
            raise

    def stt(self, audio_file, model: str | None = None) -> str:
        """
        Perform speech-to-text on an audio file.

        Args:
            audio_file: File-like object or bytes of audio

        Returns:
            Transcribed text
        """
        model = model or settings.ROUTERAI_STT_MODEL

        try:
            if hasattr(audio_file, 'read'):
                audio_data = audio_file.read()
            else:
                audio_data = audio_file

            response = self.client.audio.transcriptions.create(
                model=model,
                file=io.BytesIO(audio_data),
            )
            return response.text

        except Exception as e:
            logger.error(f"RouterAI STT error: {e}")
            raise
