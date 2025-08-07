# prompts/prompt_manager.py
from typing import List
from models.novel import Novel
from models.character import Character

class PromptManager:
    """프롬프트 생성을 전문적으로 담당하는 클래스"""

    def get_prologue_system_prompt(self) -> str:
        return """
당신은 인간의 창의성을 보조하는 전문 소설가 AI입니다.
당신은 주어진 설정과 요구사항에 따라 소설의 프롤로그를 매우 깊이 있고, 문학적이며, 흥미롭게 작성해야 합니다.
독자가 다음 챕터를 궁금해하도록 만드는 것이 당신의 가장 중요한 임무입니다.
"""

    def get_prologue_user_prompt(self, novel: Novel) -> str:
        settings = novel.settings
        character_info = self._format_character_info(settings.characters)
        
        return f"""
다음은 내가 구상 중인 소설의 핵심 설정입니다. 이 설정을 바탕으로 소설의 프롤로그를 작성해주세요.

### 1. 소설의 기본 설정
- **문체:** {settings.style}
- **시점:** {settings.pov}
- **시간적 배경:** {settings.time_bg}
- **공간적 배경:** {settings.space_bg}
- **사회적 배경:** {settings.social_bg}

### 2. 핵심 등장인물
{character_info}

### 3. 작성 요구사항
- 분량: 약 **{settings.prologue_length}** 단어 내외로 작성해주세요.
- 목표: 소설의 전반적인 분위기를 설정하고, 주요 등장인물 중 최소 한 명을 소개하며, 핵심적인 사건이나 갈등의 시작을 암시해주세요.
- 형식: 소설 본문만 작성하고, 다른 부가적인 설명은 제외해주세요.
"""

    def get_next_chapter_system_prompt(self) -> str:
        return """
당신은 이미 진행 중인 소설의 다음 챕터를 이어 쓰는 전문 소설가 AI입니다.
당신은 주어진 컨텍스트(전체 요약, 관련 챕터 내용, 직전 챕터 내용)를 완벽하게 이해하고,
소설의 일관성을 유지하면서도 흥미로운 다음 챕터를 작성해야 합니다.
"""

    def get_next_chapter_user_prompt(self, novel: Novel, rag_context: List[str]) -> str:
        settings = novel.settings
        character_info = self._format_character_info(settings.characters)

        rag_formatted_context = "\n".join(f"- {text}" for text in rag_context)

        return f"""
아래의 정보를 바탕으로 소설의 다음 챕터를 이어서 작성해주세요.

### 1. 소설의 기본 설정 (일관성 유지를 위해 참고)
- **문체:** {settings.style}
- **시점:** {settings.pov}
- **핵심 등장인물:**
{character_info}

### 2. 현재까지의 소설 전체 요약
{novel.summary}

### 3. 현재 작성할 챕터와 관련된 내용 (RAG 검색 결과)
{rag_formatted_context}

### 4. 바로 직전 챕터 내용
{novel.last_chapter_text}

### 5. 작성 요구사항
- 분량: 약 **{settings.chapter_length}** 단어 내외로 작성해주세요.
- 목표: 직전 챕터의 내용과 자연스럽게 이어지도록 스토리를 전개해주세요. 새로운 사건을 만들거나, 기존의 갈등을 심화시키거나, 인물 간의 관계에 변화를 주세요.
- 형식: 소설 본문만 작성하고, 다른 부가적인 설명은 제외해주세요.
"""

    def get_summarize_system_prompt(self) -> str:
        return "당신은 긴 글의 핵심 내용을 정확하고 간결하게 요약하는 AI입니다."

    def get_summarize_user_prompt(self, full_text: str) -> str:
        return f"""
다음은 소설의 전체 텍스트입니다. 이 내용의 핵심 줄거리, 등장인물, 주요 사건을 포함하여 200단어 내외의 요약문 작성해주세요. 이 요약문은 다음 챕터를 작성할 때 AI가 참고할 '기억'으로 사용됩니다.

--- 소설 본문 ---
{full_text}
"""

    def _format_character_info(self, characters: List[Character]) -> str:
        if not characters:
            return "아직 설정된 등장인물이 없습니다."
        
        info_lines = []
        for char in characters:
            personality_str = ", ".join(char.personality)
            appearance_str = ", ".join(char.appearance)
            info_lines.append(f"- **이름:** {char.name}\n  - **성격:** {personality_str}\n  - **외모:** {appearance_str}")
        return "\n".join(info_lines)

