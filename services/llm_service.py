# services/llm_service.py

from typing import List, Dict, Any
from ..llm_client import LLMClient # <-- 상위 디렉토리의 llm_client.py를 참조하도록 수정
from ..faiss_manager import FaissManager # <-- 상위 디렉토리의 faiss_manager.py를 참조하도록 수정
from ..prompts.prompt_manager import PromptManager # <-- 상위 디렉토리의 prompts/prompt_manager.py를 참조하도록 수정
from ..config import LLM_MODELS # <-- 상위 디렉토리의 config.py를 참조하도록 수정
from ..novel_data_manager import Novel # <-- 이전에 수정했던 부분

class LLMService:
    def __init__(self, llm_clients: Dict[str, LLMClient], prompt_manager: PromptManager, faiss_manager: FaissManager):
        self.llm_clients = llm_clients
        self.prompt_manager = prompt_manager
        self.faiss_manager = faiss_manager
        self.active_client: LLMClient = None
        self.active_model_id: str = ""

    def set_active_model(self, model_id: str):
        """활성화할 모델과 클라이언트를 설정합니다."""
        model_info = LLM_MODELS.get(model_id)
        if not model_info:
            raise ValueError(f"지원되지 않는 모델 ID: {model_id}")
        
        provider = model_info["provider"]
        if provider not in self.llm_clients:
            raise ValueError(f"'{provider}' 제공자의 클라이언트가 초기화되지 않았습니다.")
        
        self.active_client = self.llm_clients[provider]
        self.active_model_id = model_id

    def generate_prologue(self, novel: Novel) -> tuple[Novel, Dict[str, Any]]:
        """프롤로그를 생성하고 소설 객체를 업데이트합니다."""
        full_prompt = self.prompt_manager.get_prologue_prompt(novel)
        
        content, input_tokens, output_tokens = self.active_client.generate_content(
            model_id=self.active_model_id,
            prompt=full_prompt
        )
        
        tokens = {
            "prompt_tokens": input_tokens,
            "completion_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens
        }
        
        if "오류 발생" not in content:
            novel.add_chapter(content)
            novel.summary = self.active_client.summarize_novel(novel.get_full_text(), self.active_model_id)
        
        return novel, tokens

    def generate_next_chapter(self, novel: Novel) -> tuple[Novel, Dict[str, Any]]:
        """다음 챕터를 생성하고 소설 객체를 업데이트합니다."""
        relevant_memos = self.faiss_manager.search_memos_by_query(novel.next_chapter_prompt)
        full_prompt = self.prompt_manager.get_next_chapter_prompt(
            novel,
            relevant_memos,
            user_instruction=novel.next_chapter_prompt
        )
        
        content, input_tokens, output_tokens = self.active_client.generate_content(
            model_id=self.active_model_id,
            prompt=full_prompt
        )
        
        tokens = {
            "prompt_tokens": input_tokens,
            "completion_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens
        }
        
        if "오류 발생" not in content:
            novel.add_chapter(content)
            novel.summary = self.active_client.summarize_novel(novel.get_full_text(), self.active_model_id)
            self.faiss_manager.add_chapter_to_index(novel.last_chapter)

        return novel, tokens
