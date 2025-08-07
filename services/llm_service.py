from models.novel import Novel
from typing import List, Dict

class LLMService:
    def __init__(self, llm_client, prompt_manager):
        self.client = llm_client
        self.prompt_manager = prompt_manager

    def get_available_models(self) -> Dict[str, str]:
        """
        Gemini API에서 사용 가능한 모델 목록을 가져옵니다.
        """
        raw_models = self.client.list_models()
        available_models = {}
        for model in raw_models:
            if 'generateContent' in model.supported_generation_methods:
                display_name = model.display_name
                model_id = model.name.split('/')[1]
                available_models[display_name] = model_id
        return available_models

    def generate_prologue(self, settings, model_id):
        """
        프롤로그를 생성하고 요약합니다.
        """
        prompt = self.prompt_manager.get_prologue_prompt(settings)
        content = self.client.generate_content(model_id, prompt)
        summary = self.prompt_manager.summarize_novel(content)
        return content, summary

    def generate_next_chapter(self, novel: Novel, model_id: str):
        """
        다음 챕터를 생성합니다.
        """
        prompt = self.prompt_manager.get_next_chapter_prompt(novel)
        content = self.client.generate_content(model_id, prompt)
        novel.add_chapter(content)
        novel.update_summary(self.prompt_manager.summarize_novel(novel.get_full_text()))
