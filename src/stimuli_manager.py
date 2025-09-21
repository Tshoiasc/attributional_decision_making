import csv
import random
from typing import Dict, List, Optional, Tuple


class StimuliManager:
    """管理题库并确保题目不重复"""

    def __init__(self, csv_path: str) -> None:
        self._csv_path = csv_path
        self._moral: List[str] = []
        self._immoral: List[str] = []
        self._available_moral: List[str] = []
        self._available_immoral: List[str] = []
        self._load()
        self.reset_session()

    def _load(self) -> None:
        with open(self._csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            expected_columns = {"moral", "immoral"}
            if set(reader.fieldnames or []) != expected_columns:
                raise ValueError("题库文件必须包含 moral 和 immoral 两列")
            for row in reader:
                moral_text = row.get("moral", "").strip()
                immoral_text = row.get("immoral", "").strip()
                if moral_text:
                    self._moral.append(moral_text)
                if immoral_text:
                    self._immoral.append(immoral_text)

    def reset_session(self) -> None:
        self._available_moral = self._moral.copy()
        self._available_immoral = self._immoral.copy()
        random.shuffle(self._available_moral)
        random.shuffle(self._available_immoral)

    @property
    def total_questions(self) -> int:
        return len(self._moral) + len(self._immoral)

    def remaining(self) -> Dict[str, int]:
        return {
            "moral": len(self._available_moral),
            "immoral": len(self._available_immoral),
        }

    def take_first_question(self) -> Tuple[str, str]:
        """随机取第一道题，优先均衡两类"""
        pools = []
        if self._available_moral:
            pools.append("moral")
        if self._available_immoral:
            pools.append("immoral")
        if not pools:
            raise ValueError("题库已耗尽，无法继续实验")
        category = random.choice(pools)
        return self._take_from_category(category), category

    def take_second_question(self) -> Optional[Tuple[str, str]]:
        """从剩余题目中随机取第二道题，可能为无"""
        candidates: List[Tuple[str, str]] = []
        if self._available_moral:
            candidates.append(("moral", self._available_moral[-1]))
        if self._available_immoral:
            candidates.append(("immoral", self._available_immoral[-1]))
        if not candidates:
            return None
        category, _ = random.choice(candidates)
        return self._take_from_category(category), category

    def _take_from_category(self, category: str) -> str:
        pool = self._available_moral if category == "moral" else self._available_immoral
        if not pool:
            raise ValueError(f"{category} 类题目已经用尽")
        index = random.randrange(len(pool))
        return pool.pop(index)
