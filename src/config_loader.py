import json
import os
from typing import Any, Dict, List, Optional, Tuple


class ConfigError(Exception):
    """配置加载异常"""


class Config:
    """读取并校验实验配置"""

    def __init__(self, path: str) -> None:
        self._path = path
        self._raw: Dict[str, Any] = {}
        self.window: Dict[str, Any] = {}
        self.rating: Dict[str, Any] = {}
        self.timing: Dict[str, Any] = {}
        self.experiment: Dict[str, Any] = {}
        self.colors: Dict[str, Tuple[int, int, int]] = {}
        self.fonts: Dict[str, int] = {}
        self.texts: Dict[str, Any] = {}
        self.display: Dict[str, bool] = {}
        self.font_path: Optional[str] = None
        self.latin_square: Dict[str, Any] = {}
        self.question_display: Dict[str, Any] = {}
        self._load()

    @property
    def raw(self) -> Dict[str, Any]:
        return self._raw

    def _load(self) -> None:
        if not os.path.exists(self._path):
            raise ConfigError(f"未找到配置文件: {self._path}")

        with open(self._path, "r", encoding="utf-8") as f:
            try:
                self._raw = json.load(f)
            except json.JSONDecodeError as exc:
                raise ConfigError(f"配置文件解析失败: {exc}") from exc

        try:
            self.window = self._raw["window"]
            self.rating = self._raw["rating"]
            self.timing = self._raw["timing"]
            self.experiment = self._raw["experiment"]
            self.colors = self._normalize_colors(self._raw.get("colors", {}))
            self.fonts = self._raw.get("fonts", {})
            self.texts = self._raw.get("texts", {})
            self.display = self._normalize_display(self._raw.get("display", {}))
            self.font_path = self._resolve_path(self.fonts.get("path"))
            self.latin_square = self._parse_latin_square(self._raw.get("latin_square"))
            self.question_display = self._raw.get("question_display", {})
        except KeyError as exc:
            raise ConfigError(f"配置缺失必需字段: {exc}") from exc

        self._validate()

    def _parse_latin_square(self, raw_conf: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """解析拉丁方配置"""
        default_conf = {
            "enabled": False,
            "symbols": {},
            "rules": [],
            "stimuli_rules": [],
            "independent_question": False,
        }
        if raw_conf is None:
            return default_conf
        if not isinstance(raw_conf, dict):
            raise ConfigError("latin_square 配置必须为对象")

        enabled = bool(raw_conf.get("enabled", False))
        symbols = raw_conf.get("symbols", {})
        if symbols is None:
            symbols = {}
        if not isinstance(symbols, dict):
            raise ConfigError("latin_square.symbols 必须为对象")
        normalized_symbols: Dict[str, str] = {}
        for key, value in symbols.items():
            if not isinstance(key, str) or not key:
                raise ConfigError("latin_square.symbols 的键必须为非空字符串")
            if len(key.strip()) != len(key):
                raise ConfigError("latin_square.symbols 的符号不能包含首尾空格")
            normalized_symbols[key] = str(value) if value is not None else ""

        def parse_rules_array(name: str, raw_list: Any) -> List[Dict[str, Any]]:
            if raw_list is None:
                return []
            if not isinstance(raw_list, list):
                raise ConfigError(f"latin_square.{name} 必须为数组")
            parsed: List[Dict[str, Any]] = []
            for entry in raw_list:
                if isinstance(entry, str):
                    code = entry.strip()
                    if not code:
                        raise ConfigError(f"latin_square.{name} 中存在空的规则字符串")
                    parsed.append({"code": code, "probability": None})
                elif isinstance(entry, dict):
                    code = entry.get("code")
                    if not isinstance(code, str) or not code.strip():
                        raise ConfigError(f"latin_square.{name} 中的对象缺少有效的 code")
                    code = code.strip()
                    probability = entry.get("probability")
                    if probability is not None:
                        try:
                            probability = float(probability)
                        except (TypeError, ValueError) as exc:
                            raise ConfigError(f"latin_square.{name}.probability 必须为数值") from exc
                        if probability < 0:
                            raise ConfigError(f"latin_square.{name}.probability 不能为负数")
                    parsed.append({"code": code, "probability": probability})
                else:
                    raise ConfigError(f"latin_square.{name} 每一项必须为字符串或对象")
            return parsed

        rules = parse_rules_array("rules", raw_conf.get("rules", []))
        stimuli_rules = parse_rules_array("stimuli_rules", raw_conf.get("stimuli_rules"))

        independent = bool(raw_conf.get("independent_question", False))

        return {
            "enabled": enabled,
            "symbols": normalized_symbols,
            "rules": rules,
            "stimuli_rules": stimuli_rules,
            "independent_question": independent,
        }

    def _normalize_colors(self, colors: Dict[str, Any]) -> Dict[str, Tuple[int, int, int]]:
        normalized: Dict[str, Tuple[int, int, int]] = {}
        for key, value in colors.items():
            if not isinstance(value, list) or len(value) != 3:
                raise ConfigError(f"颜色配置格式错误: {key}")
            normalized[key] = tuple(int(channel) for channel in value)
        return normalized

    def _normalize_display(self, display: Dict[str, Any]) -> Dict[str, bool]:
        defaults = {
            "show_timer": True,
            "show_participant_info": True,
            "show_debug": False,
        }
        normalized: Dict[str, bool] = {}
        for key, default in defaults.items():
            value = display.get(key, default) if isinstance(display, dict) else default
            normalized[key] = bool(value)
        return normalized

    def _resolve_path(self, relative: Optional[str]) -> Optional[str]:
        if not relative:
            return None
        if os.path.isabs(relative):
            return relative
        base = os.path.dirname(self._path)
        return os.path.join(base, relative)

    def _validate(self) -> None:
        min_val = self.rating.get("min")
        max_val = self.rating.get("max")
        step = self.rating.get("step")
        if min_val is None or max_val is None or step is None:
            raise ConfigError("评分区间配置不完整")
        if max_val <= min_val:
            raise ConfigError("评分最大值必须大于最小值")
        if step <= 0:
            raise ConfigError("评分步长必须为正数")

        delay_range = self.timing.get("question_delay_range")
        if not isinstance(delay_range, list) or len(delay_range) != 2:
            raise ConfigError("题目延迟区间配置错误")
        if delay_range[0] < 0 or delay_range[1] < delay_range[0]:
            raise ConfigError("题目延迟区间设置不合法")

        if self.font_path and not os.path.exists(self.font_path):
            raise ConfigError(f"字体文件不存在: {self.font_path}")

        subtitles = self.texts.get("home_subtitle") if isinstance(self.texts, dict) else None
        if subtitles is not None and not isinstance(subtitles, list):
            raise ConfigError("texts.home_subtitle 必须为字符串列表")

        export_dir = self.experiment.get("export_directory")
        if not export_dir:
            raise ConfigError("请设置结果导出目录 export_directory")

        practice_trials = int(self.experiment.get("practice_trials", 0))
        formal_trials = int(self.experiment.get("formal_trials", 0))
        if practice_trials < 0 or formal_trials <= 0:
            raise ConfigError("试次数量必须为正数")

        latin = self.latin_square
        if latin.get("enabled"):
            def validate_ruleset(rules: List[Dict[str, Any]], label: str, require_non_empty: bool) -> None:
                if require_non_empty and not rules:
                    raise ConfigError(f"启用拉丁方时必须配置至少一条 {label}")
                if not rules:
                    return
                length_set = {len(rule["code"]) for rule in rules}
                if not length_set or length_set == {0}:
                    raise ConfigError(f"拉丁方 {label} 不能为空")
                if latin["symbols"]:
                    for symbol in latin["symbols"].keys():
                        if len(symbol) != 1:
                            raise ConfigError("latin_square.symbols 的键必须为单个字符")
                for rule in rules:
                    for ch in rule["code"]:
                        if latin["symbols"] and ch not in latin["symbols"]:
                            raise ConfigError(f"拉丁方 {label} 中使用了未定义的符号: {ch}")
                    prob = rule.get("probability")
                    if prob is not None and prob == float("inf"):
                        raise ConfigError("拉丁方概率配置非法")
                specified_probs = [rule["probability"] for rule in rules if rule["probability"] is not None]
                total_specified = sum(specified_probs)
                if total_specified > 1 + 1e-6:
                    raise ConfigError(f"拉丁方 {label} 的概率之和不能超过 1")
                unspecified = len(rules) - len(specified_probs)
                if unspecified > 0 and total_specified >= 1 - 1e-6:
                    raise ConfigError(f"拉丁方 {label} 中存在未声明概率的规则，但已无剩余概率可分配")

            formal_rules = latin["rules"]
            validate_ruleset(formal_rules, "rules", True)
            practice_rules = latin.get("stimuli_rules", [])
            validate_ruleset(practice_rules, "stimuli_rules", False)

            unique_rules = {rule["code"] for rule in formal_rules}
            if len(unique_rules) > formal_trials:
                raise ConfigError("拉丁方规则数量不能超过正式实验试次数")

    def ensure_stimuli_capacity(self, stimuli_manager: Any) -> None:
        """校验题库容量是否满足试次需求"""
        if self.latin_square.get("enabled"):
            if hasattr(stimuli_manager, "validate_capacity"):
                stimuli_manager.validate_capacity()
            else:
                raise ConfigError("当前 StimuliManager 不支持拉丁方容量校验")
            return

        total_questions = getattr(stimuli_manager, "total_questions", 0)
        max_trials = total_questions // 2
        requested_formal = int(self.experiment.get("formal_trials", 0))
        if requested_formal > max_trials:
            raise ConfigError(
                f"正式实验试次数({requested_formal}) 超过题目上限({max_trials})"
            )
        practice_trials = int(self.experiment.get("practice_trials", 0))
        if practice_trials > 0 and practice_trials > max_trials:
            raise ConfigError(
                f"模拟实验试次数({practice_trials}) 超过题目上限({max_trials})"
            )

    def export_path(self, filename: str) -> str:
        directory = self.experiment["export_directory"]
        os.makedirs(directory, exist_ok=True)
        return os.path.join(directory, filename)


def load_config(path: str = "config.json") -> Config:
    """便捷加载入口"""
    return Config(path)
