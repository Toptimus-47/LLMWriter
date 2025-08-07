# services/llm_service.py
from clients.llm_client import GeminiClient
from prompts.prompt_manager import PromptManager
from models.novel import Novel
from typing import List
from config import config

class LLMService:
    """LLM 호출 및 관련 로직 처리를 담당하는 서비스"""
    def __init__(self):
        self.client = GeminiClient()
        self.prompt_manager = PromptManager()
        self.model_id = config.MAIN_LLM_MODEL

    def generate_prologue(self, novel: Novel) -> str:
        """프롤로그 생성을 위한 프롬프트를 만들고 LLM을 호출합니다."""
        system_prompt = self.prompt_manager.get_prologue_system_prompt()
        user_prompt = self.prompt_manager.get_prologue_user_prompt(novel)
        
        prologue_content = self.client.generate_content(system_prompt, user_prompt, self.model_id)
        return prologue_content

    def generate_next_chapter(self, novel: Novel, rag_context: List[str]) -> str:
        """다음 챕터 생성을 위한 프롬프트를 만들고 LLM을 호출합니다."""
        system_prompt = self.prompt_manager.get_next_chapter_system_prompt()
        user_prompt = self.prompt_manager.get_next_chapter_user_prompt(novel, rag_context)
        
        next_chapter_content = self.client.generate_content(system_prompt, user_prompt, self.model_id)
        return next_chapter_content

    def summarize_text(self, text: str) -> str:
        """주어진 텍스트를 요약합니다."""
        system_prompt = self.prompt_manager.get_summarize_system_prompt()
        user_prompt = self.prompt_manager.get_summarize_user_prompt(text)

        summary = self.client.generate_content(system_prompt, user_prompt, self.model_id)
        return summary
