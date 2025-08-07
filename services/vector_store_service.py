# services/vector_store_service.py
import os
import faiss
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Tuple
from config import config

class VectorStoreService:
    """
    Faiss를 사용한 벡터 검색을 담당하는 서비스.
    각 인스턴스는 특정 소설의 디렉토리에 종속됩니다.
    """
    def __init__(self, novel_dir: str):
        self.novel_dir = novel_dir
        self.vector_store_dir = os.path.join(self.novel_dir, config.VECTOR_STORE_DIR)
        self.index_path = os.path.join(self.vector_store_dir, config.FAISS_INDEX_NAME)
        
        # 임베딩 모델은 한 번만 로드
        if not hasattr(VectorStoreService, '_model'):
             VectorStoreService._model = SentenceTransformer(config.EMBEDDING_MODEL)
        self.model = VectorStoreService._model

        self.index = None
        self.documents = [] # (chapter_index, text) 튜플 저장
        self._load_or_create_index()

    def _load_or_create_index(self):
        """인덱스 파일이 있으면 로드하고, 없으면 새로 생성합니다."""
        if os.path.exists(self.index_path):
            try:
                self.index = faiss.read_index(self.index_path)
                # 문서 데이터도 함께 로드해야 함 (간단하게 텍스트 파일로 저장)
                doc_path = f"{self.index_path}.docs.json"
                if os.path.exists(doc_path):
                    with open(doc_path, 'r', encoding='utf-8') as f:
                        self.documents = json.load(f)
            except Exception as e:
                print(f"인덱스 로드 실패, 새로 생성합니다: {e}")
                self._create_new_index()
        else:
            self._create_new_index()

    def _create_new_index(self):
        """새로운 Faiss 인덱스를 생성합니다."""
        os.makedirs(self.vector_store_dir, exist_ok=True)
        embedding_dim = self.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatL2(embedding_dim)
        self.documents = []

    def save_index(self):
        """현재 인덱스와 문서 목록을 파일에 저장합니다."""
        if self.index:
            faiss.write_index(self.index, self.index_path)
            doc_path = f"{self.index_path}.docs.json"
            with open(doc_path, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, ensure_ascii=False, indent=4)

    def add_document(self, text: str, chapter_index: int):
        """문서를 인덱스에 추가합니다."""
        if not text: return
        
        embedding = self.model.encode([text], convert_to_tensor=False)
        self.index.add(np.array(embedding, dtype=np.float32))
        self.documents.append((chapter_index, text))

    def search(self, query: str, k: int = 3) -> List[str]:
        """쿼리와 유사한 문서를 검색하여 텍스트 리스트를 반환합니다."""
        if not query or self.index.ntotal == 0:
            return []

        query_embedding = self.model.encode([query])
        _, indices = self.index.search(np.array(query_embedding, dtype=np.float32), k)
        
        results = []
        for i in indices[0]:
            if 0 <= i < len(self.documents):
                results.append(self.documents[i][1]) # (chapter_index, text)에서 text만 반환
        return results
