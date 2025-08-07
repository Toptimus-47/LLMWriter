# models/character.py
from dataclasses import dataclass, field
from typing import List

@dataclass
class Character:
    """등장인물 정보 데이터 클래스"""
    name: str
    personality: List[str] = field(default_factory=list)
    appearance: List[str] = field(default_factory=list)

    def to_dict(self):
        return {
            "name": self.name,
            "personality": self.personality,
            "appearance": self.appearance,
        }

    @staticmethod
    def from_dict(data: dict):
        return Character(
            name=data.get("name", ""),
            personality=data.get("personality", []),
            appearance=data.get("appearance", []),
        )
