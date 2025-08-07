# services/novel_service.py
from models.novel import Novel, Chapter
from services.file_service import FileService
from services.llm_service import LLMService
from services.vector_store_service import VectorStoreService
from config import config
from typing import List, Optional

class NovelService:
    """
    애플리케이션의 핵심 비즈니스 로직을 총괄하는 서비스.
    UI(Streamlit)와 데이터/LLM 서비스 간의 중재자 역할을 합니다.
    """
    def __init__(self):
        self.file_service = FileService()
        self.llm_service = LLMService()
        # VectorStoreService는 특정 소설이 로드될 때 인스턴스화됩니다.
        self.vector_store: Optional[VectorStoreService] = None

    def list_novels(self) -> List[str]:
        """저장된 모든 소설의 제목 리스트를 반환합니다."""
        return self.file_service.list_novels()

    def create_new_novel(self, title: str) -> Optional[Novel]:
        """새로운 소설 프로젝트를 생성합니다."""
        if self.file_service.create_novel_scaffold(title):
            novel = Novel(title=title)
            # 기본 설정 파일 저장
            self.file_service.save_settings(novel)
            return novel
        return None

    def load_novel(self, title: str) -> Optional[Novel]:
        """기존 소설을 불러옵니다."""
        try:
            novel = self.file_service.load_novel(title)
            novel_dir = self.file_service.get_novel_dir(title)
            self.vector_store = VectorStoreService(novel_dir)
            
            # 소설의 전체 텍스트를 기반으로 요약 정보가 없다면 생성
            if novel.chapters and not novel.summary:
                novel.summary = self.llm_service.summarize_text(novel.full_text)
            
            return novel
        except FileNotFoundError:
            return None

    def save_novel(self, novel: Novel):
        """현재 작업 중인 소설의 모든 데이터를 저장합니다."""
        # 1. 설정 저장
        self.file_service.save_settings(novel)
        
        # 2. 챕터 저장 (기존 챕터는 덮어쓰기)
        for i in range(len(novel.chapters)):
            self.file_service.save_chapter(novel, i)
            
        # 3. 벡터 DB 저장
        if self.vector_store:
            self.vector_store.save_index()

    def generate_prologue(self, novel: Novel):
        """프롤로그를 생성하고 소설 객체에 추가합니다."""
        prologue_content = self.llm_service.generate_prologue(novel)
        
        # 1. 챕터 추가
        prologue_chapter = Chapter(title="프롤로그", content=prologue_content)
        novel.chapters.append(prologue_chapter)
        
        # 2. 벡터 DB 초기화 및 프롤로그 추가
        novel_dir = self.file_service.get_novel_dir(novel.title)
        self.vector_store = VectorStoreService(novel_dir)
        self.vector_store.add_document(prologue_content, chapter_index=0)
        
        # 3. 전체 내용 요약
        novel.summary = self.llm_service.summarize_text(novel.full_text)
        
        # 4. 변경사항 저장
        self.save_novel(novel)

    def generate_next_chapter(self, novel: Novel):
        """다음 챕터를 생성하고 소설 객체에 추가합니다."""
        if not novel.last_chapter_text or not self.vector_store:
            raise ValueError("다음 챕터를 생성하기 위한 컨텍스트가 부족합니다.")

        # 1. RAG를 위한 컨텍스트 검색
        rag_context = self.vector_store.search(
            query=novel.last_chapter_text, 
            k=config.RAG_TOP_K
        )
        
        # 2. LLM을 통해 다음 챕터 내용 생성
        next_chapter_content = self.llm_service.generate_next_chapter(novel, rag_context)
        
        # 3. 챕터 추가
        chapter_index = len(novel.chapters)
        new_chapter = Chapter(title=f"챕터 {chapter_index}", content=next_chapter_content)
        novel.chapters.append(new_chapter)
        
        # 4. 벡터 DB에 새 챕터 추가
        self.vector_store.add_document(next_chapter_content, chapter_index)
        
        # 5. 전체 내용 요약 업데이트
        novel.summary = self.llm_service.summarize_text(novel.full_text)
        
        # 6. 변경사항 저장
        self.save_novel(novel)
