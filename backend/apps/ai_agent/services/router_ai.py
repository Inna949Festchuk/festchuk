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


def _reasoning_extra_body() -> dict | None:
    """Disable LLM thinking unless explicitly allowed via env.

    qwen3.5-plus thinks by default (~900 reasoning tokens, +10-15s per reply);
    reasoning={'enabled': False} is the verified RouterAI switch — the older
    enable_thinking flag only partially suppresses it. Must go through
    extra_body: the OpenAI SDK has no typed ``reasoning`` parameter.
    """
    if getattr(settings, 'ROUTERAI_LLM_REASONING_ENABLED', False):
        return None
    return {'reasoning': {'enabled': False}}


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
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> tuple[str, int]:
        """
        Generate a chat completion.

        Returns:
            (response_text, tokens_used)
        """
        model = model or settings.ROUTERAI_LLM_MODEL
        if temperature is None:
            temperature = settings.ROUTERAI_LLM_TEMPERATURE
        if max_tokens is None:
            max_tokens = settings.ROUTERAI_LLM_MAX_TOKENS

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                extra_body=_reasoning_extra_body(),
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
        temperature: float | None = None,
        max_tokens: int | None = None,
    ):
        """
        Generate a chat completion with function calling support.

        Returns:
            The full response object (may contain tool_calls)
        """
        model = model or settings.ROUTERAI_LLM_MODEL
        if temperature is None:
            temperature = settings.ROUTERAI_LLM_TEMPERATURE
        if max_tokens is None:
            max_tokens = settings.ROUTERAI_LLM_MAX_TOKENS

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
                extra_body=_reasoning_extra_body(),
            )
            return response

        except Exception as e:
            logger.error(f"RouterAI tool calling error: {e}")
            raise

    def chat_completion_stream(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ):
        """
        Generate a streaming chat completion.

        Returns:
            An iterator of ChatCompletionChunk objects: content deltas arrive
            live, tool calls as indexed fragments, and the final chunk carries
            usage (RouterAI sends it by default).
        """
        model = model or settings.ROUTERAI_LLM_MODEL
        if temperature is None:
            temperature = settings.ROUTERAI_LLM_TEMPERATURE
        if max_tokens is None:
            max_tokens = settings.ROUTERAI_LLM_MAX_TOKENS

        # Do NOT set stream_options.include_usage: RouterAI then buffers the
        # whole reply until completion (TTFT 15.8s vs ~1s without it, measured
        # 2026-11-18). Usage arrives in the final chunk anyway.
        extra_body = _reasoning_extra_body()

        try:
            return self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
                stream=True,
                extra_body=extra_body,
            )
        except Exception as e:
            logger.error(f"RouterAI stream error: {e}")
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

    def stt(self, audio_file, model: str | None = None, language: str | None = None) -> str:
        """
        Perform speech-to-text on an audio file.

        Args:
            audio_file: File-like object (Django UploadedFile preferred — its
                filename carries the format) or raw bytes
            model: STT model (default from settings)
            language: Whisper language hint (BCP-47: 'ru', 'en', …). Pinned to
                the UI locale by the view — auto-detection mis-hears short
                Russian phrases as English ("you So, the Telegram…").

        Returns:
            Transcribed text
        """
        model = model or settings.ROUTERAI_STT_MODEL

        try:
            # The router infers the audio format from the multipart filename
            # (mp3/wav/flac/m4a/ogg/webm/aac). A nameless BytesIO made from
            # raw bytes produces a 400 "unsupported audio format", so keep the
            # original filename; default to webm (browser MediaRecorder output).
            name = None
            if hasattr(audio_file, 'read'):
                audio = io.BytesIO(audio_file.read())
                name = getattr(audio_file, 'name', None)
            else:
                audio = io.BytesIO(audio_file)
            audio.name = name or 'recording.webm'

            create_kwargs = {'model': model, 'file': audio}
            if language:
                create_kwargs['language'] = language
            response = self.client.audio.transcriptions.create(**create_kwargs)
            return response.text

        except Exception as e:
            logger.error(f"RouterAI STT error: {e}")
            raise
