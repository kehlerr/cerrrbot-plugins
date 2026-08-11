from loguru import logger
from typing import Any, Mapping

from groq import AsyncGroq
from groq.types.chat import ChatCompletion
from pydantic import ValidationError

from ..constants import REMINDER_SYSTEM_PROMPT
from ..models import ReminderParamsExtracted


class LLMHelper:

    _SYSTEM_PROMPT = REMINDER_SYSTEM_PROMPT
    _tools = [
        {
            "type": "function",
            "function": {
                "name": "extract_reminder_parameters",
                "description": "Extract scheduling parameters and clean text for a new reminder.",
                "parameters": ReminderParamsExtracted.model_json_schema()
            },
        }
    ]

    def __init__(self, llm_client: AsyncGroq, model: str) -> None:
        self._llm_client = llm_client
        self._model = model

    async def extract_reminder_params(self, context: Mapping[str, Any], user_input: str) -> ReminderParamsExtracted | None:
        system_prompt = self._prepare_system_prompt(context)
        response = await self._send_input(system_prompt, user_input)
        return self._parse_response(response)

    def _prepare_system_prompt(self, context: Mapping[str, Any]) -> str:
        return self._SYSTEM_PROMPT.format(**context)

    def _parse_response(self, chat_completion_response: ChatCompletion | None) -> ReminderParamsExtracted | None:
        if not chat_completion_response:
            return None

        message = chat_completion_response.choices[0].message
        if not message.tool_calls:
            logger.error("No tool calls returned by the model.")
            return None

        try:
            raw_json_arguments = message.tool_calls[0].function.arguments
        except IndexError:
            logger.error("No arguments returned by the model.")
            return None


        # 6. Validate the raw JSON against our Pydantic model
        try:
            validated_data = ReminderParamsExtracted.model_validate_json(raw_json_arguments)
            return validated_data
        except ValidationError as e:
            # If the LLM hallucinated the format, Pydantic catches it here
            logger.error(f"Pydantic Validation Error:\n{e.json()}")
            return None

    async def _send_input(self, system_prompt: str, user_input: str) -> ChatCompletion | None:
        try:
            return await self._llm_client.chat.completions.create(  # type: ignore
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input},
                ],
                tools=self._tools,  # type: ignore
                tool_choice={"type": "function", "function": {"name": "extract_reminder_parameters"}},
                temperature=0.1,
            )
        except Exception as exc:
            logger.exception("API Error")

        return None

