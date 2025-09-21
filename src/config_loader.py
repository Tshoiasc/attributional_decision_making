import json
import os
from typing import Any, Dict, Optional, Tuple


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
        except KeyError as exc:
            raise ConfigError(f"配置缺失必需字段: {exc}") from exc

        self._validate()

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

        delay_range = self.timing.get("second_question_delay_range")
        if not isinstance(delay_range, list) or len(delay_range) != 2:
            raise ConfigError("第二题延迟区间配置错误")
        if delay_range[0] < 0 or delay_range[1] < delay_range[0]:
            raise ConfigError("第二题延迟区间设置不合法")

        probability = self.timing.get("second_question_probability", 0)
        if not 0 <= probability <= 1:
            raise ConfigError("第二题出现概率必须在0到1之间")

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

    def ensure_stimuli_capacity(self, total_questions: int) -> None:
        """根据题目数量校验试次数量上限"""
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
