import google.generativeai as genai
from abc import ABC, abstractmethod

class BaseLLMClient(ABC):
    """모든 LLM 클라이언트의 기본 인터페이스"""
    @abstractmethod
    def list_models(self):
        pass

    @abstractmethod
    def generate_content(self, model_id, prompt):
        pass

class GeminiClient(BaseLLMClient):
    """Google Gemini API를 사용하는 클라이언트"""
    def __init__(self, api_key):
        # API 키를 생성자를 통해 주입받음
        if not api_key:
            raise ValueError("API 키가 제공되지 않았습니다.")
        genai.configure(api_key=api_key)

    def list_models(self):
        """
        Gemini API를 통해 사용 가능한 모델 목록을 가져옵니다.
        """
        return genai.list_models()

    def generate_content(self, model_id, prompt):
        """
        주어진 모델과 프롬프트로 콘텐츠를 생성합니다.
        """
        model = genai.GenerativeModel(model_id)
        response = model.generate_content(prompt)
        return response.text
