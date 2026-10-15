"""Groq structured output through its OpenAI-compatible HTTP API."""
import os

import httpx

from .provider import BaseLLMProvider, T


def strict_schema(schema):
    """Prepare Pydantic's object schemas for Groq strict JSON output."""
    if isinstance(schema, list):
        return [strict_schema(item) for item in schema]
    if not isinstance(schema, dict):
        return schema
    result = {key: strict_schema(value) for key, value in schema.items() if key != 'default'}
    if result.get('type') == 'object':
        result['additionalProperties'] = False
        result['required'] = list(result.get('properties', {}))
    return result


class GroqLLMProvider(BaseLLMProvider):
    provider_name = "groq"
    def __init__(self, model_name=None, api_key=None):
        self.model_name = model_name or os.environ.get('API_COMPONENT_GROQ_MODEL', 'openai/gpt-oss-120b')
        self.api_key = api_key or os.environ.get('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError('GROQ_API_KEY environment variable is missing.')

    def generate_structured(self, prompt: str, schema_class: type[T]) -> T:
        response = httpx.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={'Authorization': f'Bearer {self.api_key}'},
            json={
                'model': self.model_name,
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0,
                'response_format': {
                    'type': 'json_schema',
                    'json_schema': {
                        'name': schema_class.__name__,
                        'strict': True,
                        'schema': strict_schema(schema_class.model_json_schema()),
                    },
                },
            },
            timeout=httpx.Timeout(45.0, connect=5.0),
        )
        response.raise_for_status()
        choice = response.json()['choices'][0]
        if choice.get('finish_reason') != 'stop':
            raise ValueError('Groq did not complete the structured response.')
        message = choice['message']
        if message.get('refusal') or not message.get('content'):
            raise ValueError('Groq returned a refusal or an empty response.')
        return schema_class.model_validate_json(message['content'], strict=True)
