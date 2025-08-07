# clients/llm_client.py
from abc import ABC, abstractmethod
import google.generativeai as genai
from config import config

class BaseLLMClient(ABC):
    """모든 LLM 클라이언트의 추상 기본 클래스"""
    @abstractmethod
    def generate_content(self, system_prompt: str, user_prompt: str, model_id: str) -> str:
        pass

class GeminiClient(BaseLLMClient):
    """Google Gemini API를 사용하는 클라이언트"""
    def __init__(self):
        if not config.GOOGLE_API_KEY:
            raise ValueError("Google API 키가 .env 파일에 설정되지 않았습니다.")
        genai.configure(api_key=config.GOOGLE_API_KEY)

    def generate_content(self, system_prompt: str, user_prompt: str, model_id: str) -> str:
        """
        시스템 프롬프트와 사용자 프롬프트를 받아 콘텐츠를 생성합니다.
        """
        try:
            model = genai.GenerativeModel(
                model_name=model_id,
                system_instruction=system_prompt
            )
            response = model.generate_content(user_prompt)
            return response.text
        except Exception as e:
            # API 호출 관련 예외 처리
            print(f"Gemini API 호출 중 오류 발생: {e}")
            # 특정 오류 유형에 따라 더 구체적인 처리를 할 수 있습니다.
            # 예를 들어, 안전 설정에 의해 차단된 경우, 다른 메시지를 반환할 수 있습니다.
            if "response.prompt_feedback" in str(e):
                 return "생성 요청이 안전 설정에 의해 차단되었습니다. 다른 내용으로 시도해주세요."
            return f"오류가 발생하여 내용을 생성할 수 없습니다: {e}"
