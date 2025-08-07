# models/novel.py
from dataclasses import dataclass, field
from typing import List, Optional
from models.character import Character

@dataclass
class NovelSettings:
    """소설의 전반적인 설정 데이터 클래스"""
    style: str = ""
    pov: str = "3인칭 전지적"
    time_bg: str = ""
    space_bg: str = ""
    social_bg: str = ""
    prologue_length: int = 500
    chapter_length: int = 1000
    characters: List[Character] = field(default_factory=list)

    def to_dict(self):
        return {
            "style": self.style,
            "pov": self.pov,
            "time_bg": self.time_bg,
            "space_bg": self.space_bg,
            "social_bg": self.social_bg,
            "prologue_length": self.prologue_length,
            "chapter_length": self.chapter_length,
            "characters": [char.to_dict() for char in self.characters],
        }

    @staticmethod
    def from_dict(data: dict):
        return NovelSettings(
            style=data.get("style", ""),
            pov=data.get("pov", "3인칭 전지적"),
            time_bg=data.get("time_bg", ""),
            space_bg=data.get("space_bg", ""),
            social_bg=data.get("social_bg", ""),
            prologue_length=data.get("prologue_length", 500),
            chapter_length=data.get("chapter_length", 1000),
            characters=[Character.from_dict(c) for c in data.get("characters", [])],
        )

@dataclass
class Chapter:
    """챕터 데이터 클래스"""
    title: str
    content: str

@dataclass
class Novel:
    """소설 전체를 나타내는 메인 데이터 클래스"""
    title: str
    settings: NovelSettings = field(default_factory=NovelSettings)
    chapters: List[Chapter] = field(default_factory=list)
    summary: str = "" # LLM이 생성한 전체 내용 요약

    @property
    def full_text(self) -> str:
        """모든 챕터의 본문을 합쳐서 반환"""
        return "\n\n---\n\n".join([c.content for c in self.chapters])

    @property
    def last_chapter_text(self) -> Optional[str]:
        """가장 마지막 챕터의 본문만 반환"""
        return self.chapters[-1].content if self.chapters else None
