# prompts/prompt_manager.py

from typing import List
from novel_data_manager import Novel

class PromptManager:
    """LLM 프롬프트를 생성하고 관리하는 클래스"""

    def get_novel_base_prompt(self, novel: Novel) -> str:
        """소설의 기본 설정 정보를 포함한 프롬프트를 생성합니다."""
        settings = novel.settings
        characters_str = "\n".join([
            f"- 이름: {char.name}, 성격: {', '.join(char.personality)}, 외모: {', '.join(char.appearance)}"
            for char in settings.characters
        ])
        
        return f"""
        당신은 상상력이 풍부한 소설가입니다. 다음 설정에 따라 소설의 내용을 창작해주세요.
        
        ---
        
        소설 제목: {novel.title}
        
        **[소설 설정]**
        - 문체: {settings.style}
        - 시점: {settings.pov}
        - 시간적 배경: {settings.time_bg}
        - 공간적 배경: {settings.space_bg}
        - 사회적 배경: {settings.social_bg}
        
        **[등장인물]**
        {characters_str}
        
        ---
        """

    def get_prologue_prompt(self, novel: Novel) -> str:
        """프롤로그 생성을 위한 프롬프트를 생성합니다."""
        base_prompt = self.get_novel_base_prompt(novel)
        
        return f"""
        {base_prompt}
        
        **[지시]**
        위 설정을 바탕으로 소설의 프롤로그를 {novel.settings.prologue_length} 단어 내외로 작성해주세요.
        """

    def get_next_chapter_prompt(self, novel: Novel, relevant_memos: List[str], user_instruction: str = "") -> str:
        """
        다음 챕터 생성을 위한 프롬프트를 생성합니다.
        FAISS로 검색된 관련 메모리와 작가 지시를 포함합니다.
        """
        base_prompt = self.get_novel_base_prompt(novel)
        
        memos_section = ""
        if relevant_memos:
            memos_section = "\n\n**[참고할 과거 아이디어 및 내용]**\n" + "\n\n".join(relevant_memos)
            
        user_instruction_section = ""
        if user_instruction:
            user_instruction_section = f"\n\n**[작가 지시]**\n{user_instruction}"
            
        return f"""
        {base_prompt}
        
        **[현재까지의 소설 요약]**
        {novel.summary}
        
        **[최근 챕터]**
        {novel.last_chapter}
        
        {memos_section}
        {user_instruction_section}
        
        **[지시]**
        위 컨텍스트와 지시를 바탕으로 소설의 다음 챕터를 {novel.settings.chapter_length} 단어 내외로 작성해주세요.
        """
