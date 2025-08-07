from models.novel import Novel, Chapter
from typing import List, Optional
import os

class NovelService:
    def __init__(self, file_service, llm_service):
        self.file_service = file_service
        self.llm_service = llm_service

    def create_new_novel(self, title: str) -> Novel:
        novel = Novel(title=title)
        self.file_service.save_novel(novel)
        return novel

    def load_novel(self, title: str) -> Optional[Novel]:
        return self.file_service.load_novel(title)

    def list_novels(self) -> List[str]:
        return self.file_service.list_novels()

    def save_novel(self, novel: Novel):
        self.file_service.save_novel(novel)

    def generate_prologue(self, novel: Novel):
        content, summary, input_tokens, output_tokens = self.llm_service.generate_prologue(
            novel.settings, novel.settings.model_id
        )
        novel.add_chapter(content)
        novel.summary = summary
        self.save_novel(novel)
        return input_tokens, output_tokens

    def generate_next_chapter(self, novel: Novel, user_prompt: str = ""):
        input_tokens, output_tokens = self.llm_service.generate_next_chapter(novel, novel.settings.model_id, user_prompt)
        self.save_novel(novel)
        return input_tokens, output_tokens
