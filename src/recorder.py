import csv
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class QuestionRecord:
    """单题作答记录"""

    participant_name: str
    participant_age: str
    participant_gender: str
    participant_class: str
    mode: str
    trial_index: int
    question_order: int
    category: str
    stimulus: str
    symbol: Optional[str]
    rating_value: Optional[float]
    rating_started_at: Optional[float]
    rating_confirmed_at: float
    elapsed_since_display: float
    trial_elapsed_total: float
    rule_code: Optional[str] = None
    controls: Dict[str, Any] = None


class DataRecorder:
    """负责记录实验结果并导出 CSV"""

    def __init__(self, csv_path: str) -> None:
        self._csv_path = csv_path
        self._records: List[QuestionRecord] = []
        self.participant_info: Dict[str, str] = {
            "name": "",
            "age": "",
            "gender": "",
            "class": "",
        }

    def set_participant_info(self, info: Dict[str, str]) -> None:
        for key in self.participant_info.keys():
            if key in info:
                self.participant_info[key] = str(info[key])

    def record(
        self,
        mode: str,
        trial_index: int,
        question_order: int,
        category: str,
        symbol: Optional[str],
        stimulus: str,
        rating_value: Optional[float],
        rating_started_at: Optional[float],
        rating_confirmed_at: float,
        elapsed_since_display: float,
        trial_elapsed_total: float,
        rule_code: Optional[str] = None,
        controls: Optional[Dict[str, Any]] = None,
    ) -> None:
        info = self.participant_info
        control_payload = controls.copy() if controls else {}
        self._records.append(
            QuestionRecord(
                participant_name=info.get("name", ""),
                participant_age=info.get("age", ""),
                participant_gender=info.get("gender", ""),
                participant_class=info.get("class", ""),
                mode=mode,
                trial_index=trial_index,
                question_order=question_order,
                category=category,
                stimulus=stimulus,
                symbol=symbol,
                rating_value=rating_value,
                rating_started_at=rating_started_at,
                rating_confirmed_at=rating_confirmed_at,
                elapsed_since_display=elapsed_since_display,
                trial_elapsed_total=trial_elapsed_total,
                rule_code=rule_code,
                controls=control_payload,
            )
        )


    def export(self) -> Optional[str]:
        if not self._records:
            return None
        os.makedirs(os.path.dirname(self._csv_path), exist_ok=True)
        fieldnames = [
            "participant_name",
            "participant_age",
            "participant_gender",
            "participant_class",
            "mode",
            "trial_index",
            "question_order",
            "rule_code",
            "symbol",
            "category",
            "stimulus",
            "rating_value",
            "rating_started_at",
            "rating_confirmed_at",
            "elapsed_since_display",
            "trial_elapsed_total",
            "controls",
        ]
        sorted_records = sorted(
            self._records,
            key=lambda rec: (rec.mode, rec.trial_index, rec.question_order),
        )
        with open(self._csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for record in sorted_records:
                controls = record.controls or {}
                row = {
                    "participant_name": record.participant_name,
                    "participant_age": record.participant_age,
                    "participant_gender": record.participant_gender,
                    "participant_class": record.participant_class,
                    "mode": record.mode,
                    "trial_index": record.trial_index,
                    "question_order": record.question_order,
                    "rule_code": record.rule_code or "",
                    "symbol": record.symbol or "",
                    "category": record.category,
                    "stimulus": record.stimulus,
                    "rating_value": "" if record.rating_value is None else record.rating_value,
                    "rating_started_at": "" if record.rating_started_at is None else record.rating_started_at,
                    "rating_confirmed_at": record.rating_confirmed_at,
                    "elapsed_since_display": record.elapsed_since_display,
                    "trial_elapsed_total": record.trial_elapsed_total,
                    "controls": json.dumps(controls, ensure_ascii=False) if controls else "",
                }
                writer.writerow(row)
        return self._csv_path

    def clear(self) -> None:
        self._records.clear()
