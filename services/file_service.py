# services/file_service.py
import os
import json
import shutil
from typing import List
from config import config
from models.novel import Novel, NovelSettings, Chapter

class FileService:
    """
    소설 데이터의 파일 및 디렉토리 관리를 담당하는 서비스.
    각 소설은 'novels/소설제목' 디렉토리 아래에 모든 데이터를 저장합니다.
    """
    def __init__(self):
        os.makedirs(config.NOVELS_DIR, exist_ok=True)

    def get_novel_dir(self, title: str) -> str:
        """소설 제목에 해당하는 디렉토리 경로를 반환합니다."""
        return os.path.join(config.NOVELS_DIR, title)

    def list_novels(self) -> List[str]:
        """저장된 모든 소설의 제목(디렉토리명) 리스트를 반환합니다."""
        try:
            return [d for d in os.listdir(config.NOVELS_DIR) if os.path.isdir(os.path.join(config.NOVELS_DIR, d))]
        except FileNotFoundError:
            return []

    def create_novel_scaffold(self, title: str) -> bool:
        """새 소설을 위한 디렉토리 구조를 생성합니다."""
        novel_dir = self.get_novel_dir(title)
        if os.path.exists(novel_dir):
            return False # 이미 존재하는 경우
        
        os.makedirs(novel_dir)
        os.makedirs(os.path.join(novel_dir, config.CHAPTERS_DIR))
        os.makedirs(os.path.join(novel_dir, config.VECTOR_STORE_DIR))
        return True

    def save_settings(self, novel: Novel):
        """소설의 설정(settings.json)을 저장합니다."""
        novel_dir = self.get_novel_dir(novel.title)
        settings_path = os.path.join(novel_dir, config.SETTINGS_FILENAME)
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(novel.settings.to_dict(), f, ensure_ascii=False, indent=4)

    def save_chapter(self, novel: Novel, chapter_index: int):
        """특정 챕터를 파일로 저장합니다."""
        novel_dir = self.get_novel_dir(novel.title)
        chapter = novel.chapters[chapter_index]
        chapter_filename = f"{chapter_index:04d}_{chapter.title}.txt"
        chapter_path = os.path.join(novel_dir, config.CHAPTERS_DIR, chapter_filename)
        with open(chapter_path, 'w', encoding='utf-8') as f:
            f.write(chapter.content)

    def load_novel(self, title: str) -> Novel:
        """디렉토리에서 소설 전체 데이터를 불러옵니다."""
        novel_dir = self.get_novel_dir(title)
        if not os.path.isdir(novel_dir):
            raise FileNotFoundError(f"소설 디렉토리를 찾을 수 없습니다: {title}")

        # 설정 파일 로드
        settings_path = os.path.join(novel_dir, config.SETTINGS_FILENAME)
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings_data = json.load(f)
        settings = NovelSettings.from_dict(settings_data)
        
        novel = Novel(title=title, settings=settings)

        # 챕터 파일 로드
        chapters_dir = os.path.join(novel_dir, config.CHAPTERS_DIR)
        chapter_files = sorted(os.listdir(chapters_dir))
        for filename in chapter_files:
            if filename.endswith(".txt"):
                # 파일명에서 제목 추출 (예: 0000_프롤로그.txt)
                chapter_title = os.path.splitext(filename)[0].split('_', 1)[1]
                with open(os.path.join(chapters_dir, filename), 'r', encoding='utf-8') as f:
                    content = f.read()
                novel.chapters.append(Chapter(title=chapter_title, content=content))
        
        # TODO: 요약 정보도 별도 파일로 저장하고 불러오는 로직 추가 가능
        
        return novel
