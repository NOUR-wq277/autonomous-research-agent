"""Base agent class handling LLM invocation, retries, fallback models, and structured parsing."""

import json
import time
from typing import Any, Dict, List, Optional, Type, TypeVar
from google import genai
from google.genai import types
from pydantic import BaseModel
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.config.settings import get_settings
from src.utils.helpers import clean_json_string, parse_json_safely
from src.utils.logging import logger

T = TypeVar("T", bound=BaseModel)


class BaseAgent:
    """Base class for specialized LLM agents in the research pipeline."""

    def __init__(
        self,
        name: str,
        system_instruction: str,
        client: Optional[genai.Client] = None,
        mock_mode: bool = False,
    ):
        self.name = name
        self.system_instruction = system_instruction
        self.settings = get_settings()
        self.mock_mode = mock_mode
        self.client = client

        if not self.mock_mode and not self.client and self.settings.gemini_api_key:
            self.client = genai.Client(api_key=self.settings.gemini_api_key)

    def _call_llm_with_fallback(
        self,
        prompt: str,
        temperature: float = 0.3,
        response_schema: Optional[Type[BaseModel]] = None,
        json_mode: bool = False,
    ) -> str:
        """Call Gemini LLM with automatic fallback across available models and retry logic."""
        if self.mock_mode or not self.client:
            return ""

        models_to_try = self.settings.get_all_models()
        last_error = None

        for model_name in models_to_try:
            try:
                logger.debug(f"[{self.name}] Calling model '{model_name}'...")
                config_args: Dict[str, Any] = {
                    "system_instruction": self.system_instruction,
                    "temperature": temperature,
                }

                if response_schema is not None:
                    config_args["response_mime_type"] = "application/json"
                    config_args["response_schema"] = response_schema
                elif json_mode:
                    config_args["response_mime_type"] = "application/json"

                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(**config_args),
                )

                if response and response.text:
                    logger.debug(f"[{self.name}] Successfully received response from '{model_name}'.")
                    return response.text

            except Exception as e:
                err_str = str(e)
                logger.warning(
                    f"[{self.name}] Model '{model_name}' failed: {err_str[:120]}. Trying fallback..."
                )
                last_error = e
                time.sleep(1)  # brief backoff before fallback

        raise RuntimeError(f"[{self.name}] All models failed. Last error: {last_error}")

    def generate_structured_output(
        self,
        prompt: str,
        schema: Type[T],
        temperature: float = 0.2,
    ) -> T:
        """Generate and parse structured Pydantic output, with self-healing fallback."""
        if self.mock_mode or not self.client:
            raise ValueError(f"[{self.name}] Cannot generate output in mock mode without implementation override.")

        # Attempt structured output call
        try:
            raw_text = self._call_llm_with_fallback(
                prompt=prompt,
                temperature=temperature,
                response_schema=schema,
            )
            # Parse into Pydantic model
            clean_text = clean_json_string(raw_text)
            data = json.loads(clean_text)
            return schema.model_validate(data)
        except Exception as primary_err:
            logger.warning(
                f"[{self.name}] Structured schema call failed: {primary_err}. Attempting raw JSON repair prompt..."
            )

            # Repair attempt: ask model for raw JSON conforming to schema
            repair_prompt = (
                f"{prompt}\n\n"
                f"IMPORTANT: Respond ONLY with a valid JSON object matching the required schema. No markdown, no conversation.\n"
                f"JSON schema fields required: {json.dumps(schema.model_json_schema().get('properties', {}))}"
            )
            raw_text = self._call_llm_with_fallback(
                prompt=repair_prompt,
                temperature=0.1,
                json_mode=True,
            )
            clean_text = clean_json_string(raw_text)
            data = json.loads(clean_text)
            return schema.model_validate(data)
