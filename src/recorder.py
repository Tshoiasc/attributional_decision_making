import csv
import os
from dataclasses import dataclass
from typing import Dict, List, Optional


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
    rating_value: float
    rating_started_at: float
    rating_confirmed_at: float
    elapsed_since_display: float
    trial_elapsed_total: float
    second_question_presented: bool


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
        stimulus: str,
        rating_value: float,
        rating_started_at: float,
        rating_confirmed_at: float,
        elapsed_since_display: float,
        trial_elapsed_total: float,
        second_question_presented: bool,
    ) -> None:
        info = self.participant_info
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
                rating_value=rating_value,
                rating_started_at=rating_started_at,
                rating_confirmed_at=rating_confirmed_at,
                elapsed_since_display=elapsed_since_display,
                trial_elapsed_total=trial_elapsed_total,
                second_question_presented=second_question_presented,
            )
        )


    def export(self) -> Optional[str]:
        if not self._records:
            return None
        os.makedirs(os.path.dirname(self._csv_path), exist_ok=True)
        aggregated = {}
        for record in self._records:
            key = (record.mode, record.trial_index)
            if key not in aggregated:
                aggregated[key] = {
                    "participant_name": record.participant_name,
                    "participant_age": record.participant_age,
                    "participant_gender": record.participant_gender,
                    "participant_class": record.participant_class,
                    "mode": record.mode,
                    "trial_index": record.trial_index,
                    "q2_presented": False,
                }
            bucket = aggregated[key]
            prefix = "q1" if record.question_order == 1 else "q2"
            bucket[f"{prefix}_category"] = record.category
            bucket[f"{prefix}_stimulus"] = record.stimulus
            bucket[f"{prefix}_rating_value"] = record.rating_value
            bucket[f"{prefix}_rating_started_at"] = record.rating_started_at
            bucket[f"{prefix}_rating_confirmed_at"] = record.rating_confirmed_at
            bucket[f"{prefix}_elapsed_since_display"] = record.elapsed_since_display
            bucket[f"{prefix}_trial_elapsed_total"] = record.trial_elapsed_total
            if record.question_order == 2:
                bucket["q2_presented"] = True
            else:
                bucket["q2_presented"] = record.second_question_presented
        fieldnames = [
            "participant_name",
            "participant_age",
            "participant_gender",
            "participant_class",
            "mode",
            "trial_index",
            "q1_category",
            "q1_stimulus",
            "q1_rating_value",
            "q1_rating_started_at",
            "q1_rating_confirmed_at",
            "q1_elapsed_since_display",
            "q1_trial_elapsed_total",
            "q2_presented",
            "q2_category",
            "q2_stimulus",
            "q2_rating_value",
            "q2_rating_started_at",
            "q2_rating_confirmed_at",
            "q2_elapsed_since_display",
            "q2_trial_elapsed_total",
        ]
        with open(self._csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for _, data in sorted(aggregated.items(), key=lambda item: (item[0][0], item[0][1])):
                row = {name: data.get(name, "") for name in fieldnames}
                writer.writerow(row)
        return self._csv_path

    def clear(self) -> None:
        self._records.clear()
