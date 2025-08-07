import google.generativeai as genai
from abc import ABC, abstractmethod

class BaseLLMClient(ABC):
    @abstractmethod
    def list_models(self):
        pass

    @abstractmethod
    def generate_content(self, model_id, prompt):
        pass

class GeminiClient(BaseLLMClient):
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("API 키가 제공되지 않았습니다.")
        genai.configure(api_key=api_key)

    def list_models(self):
        return genai.list_models()

    def generate_content(self, model_id, prompt):
        model = genai.GenerativeModel(model_id)
        response = model.generate_content(prompt)
        
        # Get token counts from the response
        input_tokens = model.count_tokens(prompt).total_tokens
        output_tokens = model.count_tokens(response.text).total_tokens
        
        return response.text, input_tokens, output_tokens
