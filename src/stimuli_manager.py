import csv
import random
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple


class StimuliManager:
    """管理题库并确保题目调度满足配置"""

    def __init__(self, csv_path: str, config: Any) -> None:
        self._csv_path = csv_path
        self._config = config
        self._latin_conf: Dict[str, Any] = getattr(config, "latin_square", {"enabled": False})
        self._use_latin = bool(self._latin_conf.get("enabled"))
        self._independent_questions = bool(self._latin_conf.get("independent_question", False))

        # 通用状态
        self.current_rule_code: Optional[str] = None
        self._pending_second_symbol: Optional[str] = None
        self._pending_second_text: Optional[str] = None
        self._session_rules: List[str] = []
        self._session_rule_index: int = -1
        self._unique_rule_codes: List[str] = []
        self._preassigned_trials: List[Dict[str, Tuple[Optional[str], str]]] = []

        if self._use_latin:
            self._rules: List[Dict[str, Any]] = list(self._latin_conf.get("rules", []))
            self._rule_weights: List[float] = self._compute_rule_weights(self._rules)
            self._active_symbols: List[str] = sorted(self._collect_active_symbols(self._rules))
            self._symbol_items: Dict[str, List[str]] = {}
            self._available_symbol_items: Dict[str, List[str]] = {}
            self._unique_rule_codes = self._compute_unique_rule_codes(self._rules)
            self._load_latin()
        else:
            self._moral: List[str] = []
            self._immoral: List[str] = []
            self._available_moral: List[str] = []
            self._available_immoral: List[str] = []
            self._load_standard()

        self.reset_session()

    # -------------------- 载入逻辑 --------------------

    def _load_standard(self) -> None:
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

    def _load_latin(self) -> None:
        required_symbols = [symbol for symbol in self._active_symbols if symbol != "~"]
        if not required_symbols:
            raise ValueError("启用拉丁方需要至少一个有效符号")

        with open(self._csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames or []
            missing = [symbol for symbol in required_symbols if symbol not in header]
            if missing:
                raise ValueError(f"题库缺少以下列：{', '.join(missing)}")
            for row in reader:
                for symbol in required_symbols:
                    text = row.get(symbol, "").strip()
                    if text:
                        bucket = self._symbol_items.setdefault(symbol, [])
                        bucket.append(text)
        for symbol in required_symbols:
            if not self._symbol_items.get(symbol):
                raise ValueError(f"符号 {symbol} 未提供任何题干")

    # -------------------- 公开接口 --------------------

    def reset_session(
        self,
        mode: Optional[str] = None,
        trial_count: Optional[int] = None,
        forced_sequence: Optional[List[str]] = None,
    ) -> None:
        """重置题目池，并在需要时为新的会话准备规则序列"""
        self.current_rule_code = None
        self._pending_second_symbol = None
        self._pending_second_text = None
        self._session_rules = []
        self._session_rule_index = -1
        self._preassigned_trials = []

        if self._use_latin:
            self._available_symbol_items = {
                symbol: items.copy()
                for symbol, items in self._symbol_items.items()
            }
            for items in self._available_symbol_items.values():
                random.shuffle(items)
            if forced_sequence is not None:
                if self._independent_questions:
                    base_counts = {
                        symbol: len(items) for symbol, items in self._available_symbol_items.items()
                    }
                    self._validate_sequence_feasible(forced_sequence, base_counts)
                self._session_rules = forced_sequence.copy()
            elif mode and trial_count:
                self._session_rules = self._build_rule_sequence(trial_count)
            self._session_rule_index = -1
        else:
            self._available_moral = self._moral.copy()
            self._available_immoral = self._immoral.copy()
            random.shuffle(self._available_moral)
            random.shuffle(self._available_immoral)

    @property
    def total_questions(self) -> int:
        if self._use_latin:
            return sum(len(items) for items in self._symbol_items.values())
        return len(self._moral) + len(self._immoral)

    def remaining(self) -> Dict[str, int]:
        if self._use_latin:
            return {symbol: len(items) for symbol, items in self._available_symbol_items.items()}
        return {
            "moral": len(self._available_moral),
            "immoral": len(self._available_immoral),
        }

    def validate_capacity(self) -> None:
        """校验题库是否支撑配置的试次数与规则组合"""
        practice_trials = (
            len(self._unique_rule_codes)
            if self._use_latin
            else int(self._config.experiment.get("practice_trials", 0))
        )
        formal_trials = int(self._config.experiment.get("formal_trials", 0))

        if not self._use_latin:
            total = self.total_questions
            max_trials = total // 2
            if formal_trials > max_trials:
                raise ValueError(
                    f"正式实验试次数({formal_trials}) 超过题库题目上限({max_trials})"
                )
            if practice_trials > 0 and practice_trials > max_trials:
                raise ValueError(
                    f"模拟实验试次数({practice_trials}) 超过题库题目上限({max_trials})"
                )
            return

        # 拉丁方情境
        if len(self._rules) > formal_trials:
            raise ValueError("拉丁方规则数量不能超过正式实验试次数")

        base_counts = {symbol: len(items) for symbol, items in self._symbol_items.items()}
        for symbol, count in base_counts.items():
            if count == 0:
                raise ValueError(f"符号 {symbol} 缺乏题库支持")

        if self._independent_questions:
            if formal_trials > 0:
                try:
                    self._build_rule_sequence(formal_trials, base_counts)
                except ValueError as exc:
                    raise ValueError(f"正式实验的拉丁方规则无法排布：{exc}") from exc
            if practice_trials > 0:
                try:
                    self._validate_sequence_feasible(self._unique_rule_codes, base_counts)
                except ValueError as exc:
                    raise ValueError(f"模拟实验的拉丁方规则无法排布：{exc}") from exc

    def begin_run(self, mode: str, trial_count: int) -> None:
        """为新的实验流程准备题库及规则序列"""
        if self._use_latin:
            if mode == "practice":
                sequence = self._unique_rule_codes.copy()
                if not sequence:
                    raise ValueError("拉丁方规则未配置，无法进行模拟试次")
                self.reset_session(mode=mode, trial_count=len(sequence), forced_sequence=sequence)
            else:
                self.reset_session(mode=mode, trial_count=trial_count)
            self._prepare_preassigned_trials()
        else:
            self.reset_session()

    def take_first_question(self) -> Tuple[str, str]:
        if self._use_latin:
            if not self._session_rules:
                raise ValueError("未准备拉丁方规则序列，请先调用 begin_run")
            self._session_rule_index += 1
            if self._session_rule_index >= len(self._session_rules):
                raise ValueError("当前试次数已超出预设的规则序列")
            if not self._preassigned_trials:
                raise ValueError("拉丁方题目尚未预分配")
            assignment = self._preassigned_trials[self._session_rule_index]
            first_text, first_symbol = assignment["first"]
            if first_symbol == "~" or first_text is None:
                raise ValueError("首个题目符号或题干无效")
            second_text, second_symbol = assignment["second"]
            self.current_rule_code = self._session_rules[self._session_rule_index]
            self._pending_second_symbol = second_symbol
            self._pending_second_text = second_text
            return first_text, first_symbol

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
        if self._use_latin:
            if not self.current_rule_code:
                raise ValueError("尚未呈现第一题，无法获取第二题")
            symbol = self._pending_second_symbol
            text = self._pending_second_text
            self._pending_second_symbol = None
            self._pending_second_text = None
            if not symbol or symbol == "~" or text is None:
                return None
            return text, symbol

        candidates: List[Tuple[str, str]] = []
        if self._available_moral:
            candidates.append(("moral", self._available_moral[-1]))
        if self._available_immoral:
            candidates.append(("immoral", self._available_immoral[-1]))
        if not candidates:
            return None
        category, _ = random.choice(candidates)
        return self._take_from_category(category), category

    # -------------------- 内部工具 --------------------

    def _take_from_category(self, category: str) -> str:
        pool = self._available_moral if category == "moral" else self._available_immoral
        if not pool:
            raise ValueError(f"{category} 类题目已经用尽")
        index = random.randrange(len(pool))
        return pool.pop(index)

    def _take_from_symbol(self, symbol: str) -> str:
        pool = self._available_symbol_items.get(symbol)
        if not pool:
            raise ValueError(f"符号 {symbol} 的题目已经用尽")
        return pool.pop()

    def _compute_rule_weights(self, rules: List[Dict[str, Any]]) -> List[float]:
        if not rules:
            return []
        specified_sum = sum(rule["probability"] for rule in rules if rule.get("probability") is not None)
        unspecified_count = sum(1 for rule in rules if rule.get("probability") is None)
        weights: List[float] = []

        if unspecified_count == 0:
            if specified_sum == 0:
                return [1.0 / len(rules)] * len(rules)
            return [rule.get("probability", 0.0) / specified_sum for rule in rules]

        leftover = max(0.0, 1.0 - specified_sum)
        if leftover == 0 and specified_sum > 0:
            raise ValueError("概率之和已满 1，无法为未指定概率的规则分配权重")
        if leftover == 0 and specified_sum == 0:
            equal = 1.0 / len(rules)
            return [equal] * len(rules)

        default_weight = leftover / unspecified_count
        for rule in rules:
            weight = rule.get("probability")
            if weight is None:
                weight = default_weight
            weights.append(weight)
        total = sum(weights)
        if total == 0:
            return [1.0 / len(rules)] * len(rules)
        return [weight / total for weight in weights]

    def _collect_active_symbols(self, rules: List[Dict[str, Any]]) -> List[str]:
        symbols = set()
        for rule in rules:
            for char in rule["code"]:
                symbols.add(char)
        for defined in self._latin_conf.get("symbols", {}).keys():
            symbols.add(defined)
        return list(symbols)

    def _build_rule_sequence(
        self, trial_count: int, available_counts: Optional[Dict[str, int]] = None
    ) -> List[str]:
        if trial_count <= 0:
            return []
        if not self._rules:
            raise ValueError("拉丁方规则未配置，无法生成序列")

        if available_counts is None:
            if self._independent_questions:
                available_counts = {
                    symbol: len(items) for symbol, items in self._available_symbol_items.items()
                }
            else:
                available_counts = {}
        else:
            available_counts = available_counts.copy()

        usages: List[Counter] = [Counter(rule["code"]) for rule in self._rules]
        feasible_caps: List[int] = []
        if self._independent_questions:
            for usage in usages:
                cap = float("inf")
                for symbol, need in usage.items():
                    if symbol == "~":
                        continue
                    stock = available_counts.get(symbol, 0)
                    if need <= 0:
                        continue
                    cap = min(cap, stock // need if need else float("inf"))
                feasible_caps.append(int(cap) if cap != float("inf") else trial_count)
        else:
            feasible_caps = [trial_count] * len(self._rules)

        weights = self._rule_weights or [1.0 / len(self._rules)] * len(self._rules)
        if sum(weights) == 0:
            weights = [1.0 / len(self._rules)] * len(self._rules)

        raw_counts = [weight * trial_count for weight in weights]
        assigned = [0] * len(self._rules)
        fractions = [0.0] * len(self._rules)
        total_assigned = 0
        for idx, raw in enumerate(raw_counts):
            base = int(raw)
            if base > feasible_caps[idx]:
                base = feasible_caps[idx]
            assigned[idx] = base
            fractions[idx] = raw - base
            total_assigned += base

        remainder = trial_count - total_assigned
        while remainder > 0:
            best_idx = -1
            best_fraction = -1.0
            for idx, frac in enumerate(fractions):
                if assigned[idx] >= feasible_caps[idx]:
                    continue
                if frac > best_fraction:
                    best_fraction = frac
                    best_idx = idx
            if best_idx == -1:
                if self._independent_questions:
                    raise ValueError("题库题量不足，无法满足设定的试次数或概率分配")
                # 非独立模式理论上不会出现
                raise ValueError("规则权重分配失败")
            assigned[best_idx] += 1
            fractions[best_idx] = 0.0
            remainder -= 1

        # 若某些 rule 的期望值为 0，但仍有剩余容量（极端情况），均分补齐
        if sum(assigned) < trial_count:
            leftover = trial_count - sum(assigned)
            for idx in range(len(self._rules)):
                if leftover == 0:
                    break
                if assigned[idx] < feasible_caps[idx]:
                    assigned[idx] += 1
                    leftover -= 1
        if sum(assigned) != trial_count:
            raise ValueError("规则计数分配异常，无法匹配试次数")

        if self._independent_questions:
            for idx, count in enumerate(assigned):
                usage = usages[idx]
                for symbol, need in usage.items():
                    if symbol == "~":
                        continue
                    available_counts[symbol] -= need * count
                    if available_counts[symbol] < 0:
                        raise ValueError("题库题量不足以满足规则分配需求")

        sequence: List[str] = []
        for idx, count in enumerate(assigned):
            sequence.extend([self._rules[idx]["code"]] * count)
        random.shuffle(sequence)
        return sequence

    def _rule_feasible(self, code: str, available_counts: Dict[str, int]) -> bool:
        usage = Counter(code)
        for symbol, count in usage.items():
            if symbol == "~":
                continue
            if available_counts.get(symbol, 0) < count:
                return False
        return True

    def _validate_sequence_feasible(
        self, sequence: List[str], available_counts: Dict[str, int]
    ) -> None:
        counts = available_counts.copy()
        for code in sequence:
            if not self._rule_feasible(code, counts):
                raise ValueError("题库题量不足以覆盖指定的规则序列")
            for symbol, usage in Counter(code).items():
                if symbol == "~":
                    continue
                counts[symbol] -= usage

    def _prepare_preassigned_trials(self) -> None:
        if not self._session_rules:
            raise ValueError("拉丁方规则序列为空，无法预分配题目")

        assignments: List[Dict[str, Tuple[Optional[str], str]]] = []
        if self._independent_questions:
            pools: Dict[str, List[str]] = {
                symbol: self._available_symbol_items.get(symbol, [])
                for symbol in self._available_symbol_items.keys()
            }
        else:
            base_lists: Dict[str, List[str]] = {
                symbol: self._symbol_items.get(symbol, []).copy()
                for symbol in self._symbol_items.keys()
            }
            for symbol, items in base_lists.items():
                if not items:
                    raise ValueError(f"符号 {symbol} 缺乏题库支持")

        def draw(symbol: str) -> Optional[str]:
            if symbol == "~":
                return None
            if self._independent_questions:
                pool = pools.get(symbol)
                if not pool:
                    raise ValueError(f"符号 {symbol} 的题目数量不足以支持非重复分配")
                return pool.pop()
            base = base_lists.get(symbol, [])
            if not base:
                raise ValueError(f"符号 {symbol} 缺乏题库支持")
            return random.choice(base)

        for code in self._session_rules:
            symbols = list(code)
            if not symbols:
                raise ValueError("拉丁方规则不能为空字符串")
            first_symbol = symbols[0]
            second_symbol = symbols[1] if len(symbols) > 1 else "~"
            first_text = draw(first_symbol)
            if first_text is None:
                raise ValueError("首题符号不允许为空")
            second_text = draw(second_symbol)
            assignments.append(
                {
                    "first": (first_text, first_symbol),
                    "second": (second_text, second_symbol),
                }
            )

        self._preassigned_trials = assignments

    def _compute_unique_rule_codes(self, rules: List[Dict[str, Any]]) -> List[str]:
        seen: Dict[str, bool] = {}
        unique: List[str] = []
        for rule in rules:
            code = rule.get("code", "")
            if code and code not in seen:
                seen[code] = True
                unique.append(code)
        return unique

    def get_rule_plan(self) -> List[str]:
        return self._session_rules.copy()

    def get_symbol_definitions(self) -> Dict[str, str]:
        if not self._use_latin:
            return {}
        return dict(self._latin_conf.get("symbols", {}))

    def practice_trial_count(self) -> int:
        if self._use_latin:
            return len(self._unique_rule_codes)
        return int(self._config.experiment.get("practice_trials", 0))

    def get_rule_weights(self) -> List[Tuple[str, float, Optional[float]]]:
        if not self._use_latin:
            return []
        result: List[Tuple[str, float, Optional[float]]] = []
        for rule, weight in zip(self._rules, self._rule_weights):
            result.append((rule.get("code", ""), weight, rule.get("probability")))
        return result

    def is_independent_mode(self) -> bool:
        return bool(self._independent_questions) if self._use_latin else True
