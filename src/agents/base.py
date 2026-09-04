"""Base agent class handling LLM invocation, retries, fallback models, and structured parsing."""

import json
import time
from typing import Any, Dict, List, Optional, Type, TypeVar
from google import genai
from google.genai import types
from pydantic import BaseModel

from src.config.settings import get_settings
from src.utils.helpers import clean_json_string
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
        temperature: float = 0.2,
        response_schema: Optional[Type[BaseModel]] = None,
        json_mode: bool = False,
    ) -> str:
        """Call Gemini LLM with automatic fallback across available models and retry logic."""
        if self.mock_mode:
            return ""

        if not self.client:
            raise ValueError(
                f"[{self.name}] Gemini client is not initialized. Please set GEMINI_API_KEY in your .env file."
            )

        models_to_try = self.settings.get_all_models()
        last_error = None

        for model_name in models_to_try:
            for attempt in range(2):
                try:
                    logger.debug(f"[{self.name}] Invoking model '{model_name}' (attempt {attempt+1})...")
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
                    last_error = e

                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        logger.warning(
                            f"[{self.name}] Rate limit (429) hit on '{model_name}'. Pausing for 8 seconds before retry..."
                        )
                        time.sleep(8)
                        continue
                    elif "503" in err_str or "UNAVAILABLE" in err_str:
                        logger.warning(
                            f"[{self.name}] Model '{model_name}' high demand (503). Trying fallback model..."
                        )
                        break
                    else:
                        logger.warning(
                            f"[{self.name}] Model '{model_name}' error: {err_str[:120]}. Trying fallback model..."
                        )
                        time.sleep(1)
                        break

        raise RuntimeError(f"[{self.name}] All configured Gemini models failed. Last error: {last_error}")

    def generate_structured_output(
        self,
        prompt: str,
        schema: Type[T],
        temperature: float = 0.2,
    ) -> T:
        """Generate and parse structured Pydantic output with real-time schema validation."""
        if self.mock_mode:
            raise ValueError(f"[{self.name}] Cannot generate output in mock mode without explicit override.")

        # Attempt structured output call
        try:
            raw_text = self._call_llm_with_fallback(
                prompt=prompt,
                temperature=temperature,
                response_schema=schema,
            )
            clean_text = clean_json_string(raw_text)
            data = json.loads(clean_text)
            return schema.model_validate(data)
        except Exception as primary_err:
            logger.warning(
                f"[{self.name}] Direct structured output call failed: {primary_err}. Initiating JSON self-healing repair..."
            )

            # Repair attempt: raw JSON with explicit schema definition
            properties = schema.model_json_schema().get("properties", {})
            repair_prompt = (
                f"{prompt}\n\n"
                f"CRITICAL: Respond ONLY with a valid, parseable JSON object adhering to this schema:\n"
                f"{json.dumps(properties, indent=2)}\n"
                f"No markdown formatting, no conversational filler."
            )
            raw_text = self._call_llm_with_fallback(
                prompt=repair_prompt,
                temperature=0.1,
                json_mode=True,
            )
            clean_text = clean_json_string(raw_text)
            data = json.loads(clean_text)
            return schema.model_validate(data)
