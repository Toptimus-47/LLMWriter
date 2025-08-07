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
        # generateContent 메서드를 지원하는 모델만 필터링
        if 'generateContent' in model.supported_generation_methods:
            # 사용자에게 보여줄 이름과 실제 API에 사용할 ID를 분리
            display_name = model.display_name
            
            # 여기서 model.name을 그대로 사용해야 합니다.
            # model.name은 이미 'models/gemini-1.5-pro'와 같은 형식을 가지고 있습니다.
            model_id = model.name
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
