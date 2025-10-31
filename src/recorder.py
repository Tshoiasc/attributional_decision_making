import csv
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
    rating_value: float
    rating_started_at: float
    rating_confirmed_at: float
    elapsed_since_display: float
    trial_elapsed_total: float
    second_question_presented: bool
    rule_code: Optional[str] = None


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
        rule_code: Optional[str] = None,
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
                rule_code=rule_code,
            )
        )


    def export(self) -> Optional[str]:
        if not self._records:
            return None
        os.makedirs(os.path.dirname(self._csv_path), exist_ok=True)
        aggregated = {}
        max_questions = 0
        
        # 第一次遍历：聚合数据并找出最大题目数
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
                    "rule_code": "",
                    "questions": {},
                }
            bucket = aggregated[key]
            if record.rule_code and not bucket.get("rule_code"):
                bucket["rule_code"] = record.rule_code
            
            # 使用动态的题目编号
            q_num = record.question_order
            if q_num > max_questions:
                max_questions = q_num
            
            if q_num not in bucket["questions"]:
                bucket["questions"][q_num] = {}
            
            bucket["questions"][q_num] = {
                "category": record.category,
                "stimulus": record.stimulus,
                "rating_value": record.rating_value,
                "rating_started_at": record.rating_started_at,
                "rating_confirmed_at": record.rating_confirmed_at,
                "elapsed_since_display": record.elapsed_since_display,
                "trial_elapsed_total": record.trial_elapsed_total,
            }
        
        # 构建字段名
        fieldnames = [
            "participant_name",
            "participant_age",
            "participant_gender",
            "participant_class",
            "mode",
            "trial_index",
            "rule_code",
            "num_questions",
        ]
        
        # 为每个可能的题目位置添加字段
        for q_num in range(1, max_questions + 1):
            fieldnames.extend([
                f"q{q_num}_category",
                f"q{q_num}_stimulus",
                f"q{q_num}_rating_value",
                f"q{q_num}_rating_started_at",
                f"q{q_num}_rating_confirmed_at",
                f"q{q_num}_elapsed_since_display",
                f"q{q_num}_trial_elapsed_total",
            ])
        
        # 写入CSV
        with open(self._csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for _, data in sorted(aggregated.items(), key=lambda item: (item[0][0], item[0][1])):
                row: Dict[str, Any] = {
                    "participant_name": data.get("participant_name", ""),
                    "participant_age": data.get("participant_age", ""),
                    "participant_gender": data.get("participant_gender", ""),
                    "participant_class": data.get("participant_class", ""),
                    "mode": data.get("mode", ""),
                    "trial_index": data.get("trial_index", ""),
                    "rule_code": data.get("rule_code", ""),
                    "num_questions": len(data.get("questions", {})),
                }
                
                # 填充每个题目的数据
                questions = data.get("questions", {})
                for q_num in range(1, max_questions + 1):
                    if q_num in questions:
                        q_data = questions[q_num]
                        row[f"q{q_num}_category"] = q_data.get("category", "")
                        row[f"q{q_num}_stimulus"] = q_data.get("stimulus", "")
                        row[f"q{q_num}_rating_value"] = q_data.get("rating_value", "")
                        row[f"q{q_num}_rating_started_at"] = q_data.get("rating_started_at", "")
                        row[f"q{q_num}_rating_confirmed_at"] = q_data.get("rating_confirmed_at", "")
                        row[f"q{q_num}_elapsed_since_display"] = q_data.get("elapsed_since_display", "")
                        row[f"q{q_num}_trial_elapsed_total"] = q_data.get("trial_elapsed_total", "")
                    else:
                        row[f"q{q_num}_category"] = ""
                        row[f"q{q_num}_stimulus"] = ""
                        row[f"q{q_num}_rating_value"] = ""
                        row[f"q{q_num}_rating_started_at"] = ""
                        row[f"q{q_num}_rating_confirmed_at"] = ""
                        row[f"q{q_num}_elapsed_since_display"] = ""
                        row[f"q{q_num}_trial_elapsed_total"] = ""
                
                writer.writerow(row)
        return self._csv_path

    def clear(self) -> None:
        self._records.clear()
