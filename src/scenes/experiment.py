import random
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pygame

from src.recorder import DataRecorder
from src.stimuli_manager import StimuliManager
from src.ui.button import Button
from src.ui.slider import Slider


class ExperimentScene:
    """实验流程场景，负责控制题目呈现与数据记录"""

    def __init__(
        self,
        screen: pygame.Surface,
        config,
        fonts: Dict[str, pygame.font.Font],
        stimuli: StimuliManager,
        recorder: DataRecorder,
        mode: str,
        participant_info: Dict[str, str],
        scale: float,
        on_finish,
        total_trials_override: Optional[int] = None,
    ) -> None:
        self.screen = screen
        self.config = config
        self.fonts = fonts
        self.stimuli = stimuli
        self.recorder = recorder
        self.mode = mode
        self.participant_info = participant_info
        self.scale = max(scale, 0.5)
        self.on_finish = on_finish

        self.colors = config.colors
        self.display = getattr(config, "display", {"show_timer": True, "show_participant_info": True})
        if not isinstance(self.display, dict):
            self.display = {"show_timer": True, "show_participant_info": True}
        rating_conf = config.rating
        self.latin_enabled = bool(getattr(config, "latin_square", {}).get("enabled"))
        self.show_debug = bool(self.display.get("show_debug", False))
        self.total_trials = (
            config.experiment["practice_trials"]
            if mode == "practice"
            else config.experiment["formal_trials"]
        )
        if total_trials_override is not None:
            self.total_trials = total_trials_override

        self.portrait_entries = self._load_portraits()
        if len(self.portrait_entries) < self.total_trials:
            raise ValueError(
                f"画像数量不足，至少需要 {self.total_trials} 张图片，当前仅有 {len(self.portrait_entries)} 张"
            )
        self._portrait_sequence = random.sample(self.portrait_entries, self.total_trials)
        self._portrait_index = 0
        self.current_portrait_entry: Optional[Dict[str, object]] = None
        self.current_subject_name: str = ""
        self._current_portrait_scaled: Optional[pygame.Surface] = None
        self.current_question_display: Optional[str] = None

        slider_length = int(screen.get_width() * 0.65)
        slider_x = int((screen.get_width() - slider_length) / 2)
        slider_y = int(screen.get_height() * 0.76)
        self.slider = Slider(
            start_pos=(slider_x, slider_y),
            length=slider_length,
            min_value=rating_conf["min"],
            max_value=rating_conf["max"],
            step=rating_conf["step"],
            font=self.fonts["body"],
            label_low=rating_conf.get("label_low", "内在"),
            label_high=rating_conf.get("label_high", "外在"),
            colors=(self.colors["accent"], self.colors["accent"], self.colors["disabled"]),
            label_color=self.colors["text_primary"],
            scale=self.scale,
        )

        button_font = self.fonts["body"]
        button_width = max(200, int(220 * self.scale))
        button_height = max(48, int(58 * self.scale))
        button_rect = pygame.Rect(0, 0, button_width, button_height)
        button_rect.center = (self.screen.get_width() // 2, slider_y + int(120 * self.scale))
        self.confirm_button = Button(
            rect=button_rect,
            text="确认",
            font=button_font,
            bg_color=self.colors["accent"],
            text_color=self.colors["button_text"],
            disabled_color=self.colors["disabled"],
            on_click=self._confirm_rating,
            scale=self.scale,
        )

        self.state = "transition"
        self.current_trial = 0
        self.current_question_order = 0
        self.current_question_text: Optional[str] = None
        self.current_category: Optional[str] = None
        self.current_question_confirmed = False
        self.has_real_second_question = False
        self.second_question_payload: Optional[Tuple[str, str]] = None
        self.waiting_target_time: Optional[float] = None
        self.current_rule_code: Optional[str] = None
        self._placeholder_repeat_text: Optional[str] = None
        self._current_question_highlight: Optional[str] = None
        self._current_question_segments: Tuple[Tuple[str, Tuple[int, int, int]], ...] = ()
        self.current_symbol: Optional[str] = None
        self.previous_symbol: Optional[str] = None
        self._debug_lines: Tuple[str, ...] = ()

        self.transition_start = time.perf_counter()
        self.trial_start_time = time.perf_counter()
        self.question_start_time: Optional[float] = None
        self.slider_enabled_time: Optional[float] = None
        self.experiment_start = time.perf_counter()
        self.last_confirm_time: Optional[float] = None
        self.last_question_duration: float = 0.0
        self.previous_rating_value: Optional[float] = None
        self.previous_question_raw: Optional[str] = None

        self._prepare_next_trial(initial=True)
        if self.show_debug:
            self._build_debug_lines()
            if self._debug_lines:
                self.state = "debug"

    def _prepare_next_trial(self, initial: bool = False) -> None:
        if not initial:
            self.current_trial += 1
        else:
            self.current_trial = 1

        if self.current_trial > self.total_trials:
            exported = self.recorder.export()
            self.state = "completed"
            self.completion_time = time.perf_counter()
            self.exported_file = exported
            return

        if self._portrait_index < len(self._portrait_sequence):
            self.current_portrait_entry = self._portrait_sequence[self._portrait_index]
            self._portrait_index += 1
        else:
            self.current_portrait_entry = None
        self.current_subject_name = (
            self.current_portrait_entry.get("name") if self.current_portrait_entry else ""
        )
        self._current_portrait_scaled = None
        self.current_question_display = None

        self.state = "transition"
        self.transition_start = time.perf_counter()
        self.trial_start_time = time.perf_counter()
        self.current_question_order = 0
        self.current_question_text = None
        self.current_category = None
        self.slider.reset()
        self.confirm_button.set_enabled(False)
        self.last_question_duration = 0.0
        self.has_real_second_question = False
        self.second_question_payload = None
        self.waiting_target_time = None
        self.waiting_duration = 0.0
        self.current_question_confirmed = False
        self.previous_rating_value = None
        self.previous_question_raw = None
        self.current_rule_code = None
        self._placeholder_repeat_text = None
        self._current_question_highlight = None
        self._current_question_segments = ()
        self.current_symbol = None
        self.previous_symbol = None

    def _present_first_question(self) -> None:
        text, category = self.stimuli.take_first_question()
        self._setup_question(text, category, order=1)
        self.current_rule_code = getattr(self.stimuli, "current_rule_code", None)
        delay_min, delay_max = self.config.timing["second_question_delay_range"]
        if self.latin_enabled:
            payload = self.stimuli.take_second_question()
        else:
            probability = self.config.timing["second_question_probability"]
            show_second = random.random() < probability
            if self.mode == "practice":
                if self.current_trial == 1:
                    show_second = False
                elif self.current_trial == 2:
                    show_second = True
            payload = self.stimuli.take_second_question() if show_second else None
        if payload:
            self.has_real_second_question = True
            self.second_question_payload = payload
            self._placeholder_repeat_text = None
        else:
            self.has_real_second_question = False
            base_text = self.previous_question_raw or text
            subject_prefix = self.current_subject_name or ""
            repeat_symbol = self.previous_symbol or self._category_symbol(category)
            repeat_line = f"[{repeat_symbol}] {subject_prefix}{base_text}，"
            instructions = (
                "[~] 当前无新信息。请基于上一轮次行为：\n"
                f"{repeat_line}\n"
                "考虑你是否更改当前评价"
            )
            self._placeholder_repeat_text = repeat_line
            self.second_question_payload = (instructions, "none")
        self.waiting_duration = random.uniform(delay_min, delay_max)

    def _setup_question(self, text: str, category: str, order: int) -> None:
        self.current_question_order = order
        self.current_question_text = text
        self.current_category = category
        self.current_symbol = self._category_symbol(category)
        self.question_start_time = time.perf_counter()
        self.slider_enabled_time = None
        self.current_question_confirmed = False
        self.state = "question"
        self.slider.reset()
        if order == 1:
            self.previous_question_raw = text
            self.previous_symbol = self.current_symbol
        if order == 2 and self.previous_rating_value is not None:
            self.slider.set_value(self.previous_rating_value)
        self.slider.set_enabled(True)
        self.confirm_button.set_enabled(True)
        self.slider_enabled_time = self.question_start_time
        if order == 2 and self.current_category == "none":
            self.current_question_display = text
            self._current_question_highlight = self._placeholder_repeat_text
        else:
            self.current_question_display = self._compose_question_display(text)
            self._current_question_highlight = None
        self._refresh_question_segments()

    def _confirm_rating(self) -> None:
        if self.state != "question" or not self.slider.enabled:
            return
        self.slider.set_enabled(False)
        self.confirm_button.set_enabled(False)
        self.current_question_confirmed = True
        confirm_time = time.perf_counter()
        self.last_confirm_time = confirm_time
        slider_enabled_at = self.slider_enabled_time or confirm_time
        elapsed = confirm_time - (self.question_start_time or confirm_time)
        trial_elapsed = confirm_time - self.trial_start_time
        self.last_question_duration = elapsed
        rating_value = self.slider.value
        if self.current_question_order == 1:
            self.previous_rating_value = rating_value
        self.recorder.record(
            mode=self.mode,
            trial_index=self.current_trial,
            question_order=self.current_question_order,
            category=self.current_category or "unknown",
            stimulus=self.current_question_text or "",
            rating_value=rating_value,
            rating_started_at=slider_enabled_at - self.experiment_start,
            rating_confirmed_at=confirm_time - self.experiment_start,
            elapsed_since_display=elapsed,
            trial_elapsed_total=trial_elapsed,
            second_question_presented=self.has_real_second_question,
            rule_code=self.current_rule_code if self.current_rule_code else None,
        )

        if self.current_question_order == 1:
            self.state = "waiting_second"
            self.waiting_target_time = confirm_time + self.waiting_duration
        else:
            self._prepare_next_trial()

    def _present_second_question(self) -> None:
        if not self.second_question_payload:
            self._prepare_next_trial()
            return
        text, category = self.second_question_payload
        self._setup_question(text, category, order=2)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.recorder.export()
            self.on_finish()
            return
        if self.state == "debug":
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.state = "transition"
                self.transition_start = time.perf_counter()
            return
        if self.state == "completed":
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.on_finish()
            return
        if self.state == "question":
            self.slider.handle_event(event)
            self.confirm_button.handle_event(event)

    def update(self, _dt: float) -> None:
        if self.state == "debug":
            return
        now = time.perf_counter()
        if self.state == "transition":
            if now - self.transition_start >= self.config.timing["transition_duration"]:
                self._present_first_question()
        elif self.state == "waiting_second":
            if self.waiting_target_time and now >= self.waiting_target_time:
                self._present_second_question()

    def draw(self) -> None:
        self.screen.fill(self.colors["background"])
        if self.display.get("show_participant_info", True):
            self._draw_participant_info()
        if self.display.get("show_timer", True):
            self._draw_timer()
        if self.state == "debug":
            self._draw_debug_overlay()
        elif self.state == "transition":
            self._draw_transition()
        elif self.state == "question":
            self._draw_question()
        elif self.state == "waiting_second":
            self._draw_waiting()
        elif self.state == "completed":
            self._draw_completed()


    def _draw_participant_info(self) -> None:
        font = self.fonts["body"]
        labels = [
            f"姓名：{self.participant_info.get('name', '')}",
            f"年龄：{self.participant_info.get('age', '')}",
            f"性别：{self.participant_info.get('gender', '')}",
            f"班级：{self.participant_info.get('class', '')}",
        ]
        margin_x = int(30 * self.scale)
        margin_y = int(20 * self.scale)
        line_gap = max(24, int(36 * self.scale))
        for idx, text in enumerate(labels):
            surface = font.render(text, True, self.colors["text_primary"])
            self.screen.blit(surface, (margin_x, margin_y + idx * line_gap))

    def _draw_timer(self) -> None:
        now = time.perf_counter()
        total_elapsed = now - self.experiment_start if self.state != "completed" else self.completion_time - self.experiment_start
        if self.state == "question" and not self.current_question_confirmed:
            current_elapsed = now - (self.question_start_time or now)
        else:
            current_elapsed = self.last_question_duration
        timer_font = self.fonts["body"]
        total_text = timer_font.render(f"总用时：{total_elapsed:6.2f}s", True, self.colors["text_primary"])
        current_text = timer_font.render(f"当前题目用时：{current_elapsed:5.2f}s", True, self.colors["text_primary"])
        width = self.screen.get_width()
        margin = int(30 * self.scale)
        self.screen.blit(total_text, (width - total_text.get_width() - margin, margin))
        self.screen.blit(current_text, (width - current_text.get_width() - margin, margin + int(40 * self.scale)))

    def _draw_transition(self) -> None:
        font = self.fonts["subtitle"]
        text = font.render(
            f"准备第 {self.current_trial} / {self.total_trials} 次情境评估",
            True,
            self.colors["text_primary"],
        )
        self.screen.blit(text, text.get_rect(center=(self.screen.get_width() / 2, self.screen.get_height() / 2)))

    def _draw_debug_overlay(self) -> None:
        lines = self._debug_lines or ("未启用拉丁方规则调试信息。",)
        title_font = self.fonts["subtitle"]
        body_font = self.fonts["body"]
        title = title_font.render("规则分配预览", True, self.colors["text_primary"])
        title_rect = title.get_rect(center=(self.screen.get_width() / 2, self.screen.get_height() / 2 - int(200 * self.scale)))
        self.screen.blit(title, title_rect)

        line_gap = max(30, int(36 * self.scale))
        start_y = title_rect.bottom + int(20 * self.scale)
        for idx, text in enumerate(lines):
            surface = body_font.render(text, True, self.colors["text_primary"])
            rect = surface.get_rect(center=(self.screen.get_width() / 2, start_y + idx * line_gap))
            self.screen.blit(surface, rect)

        hint = body_font.render("按 空格 / 回车 开始实验", True, self.colors["accent"])
        hint_rect = hint.get_rect(center=(self.screen.get_width() / 2, self.screen.get_height() - int(120 * self.scale)))
        self.screen.blit(hint, hint_rect)

    def _draw_question(self) -> None:
        self._draw_question_panel()
        self.slider.draw(self.screen)
        self.confirm_button.draw(self.screen)

    def _draw_waiting(self) -> None:
        center = (self.screen.get_width() // 2, self.screen.get_height() // 2)
        size = int(80 * self.scale)
        thickness = max(4, int(8 * self.scale))
        color = (0, 0, 0)
        pygame.draw.line(
            self.screen,
            color,
            (center[0] - size, center[1]),
            (center[0] + size, center[1]),
            thickness,
        )
        pygame.draw.line(
            self.screen,
            color,
            (center[0], center[1] - size),
            (center[0], center[1] + size),
            thickness,
        )

    def _draw_completed(self) -> None:
        font = self.fonts["subtitle"]
        message = "模拟实验完成" if self.mode == "practice" else "正式实验已完成"
        text = font.render(message, True, self.colors["text_primary"])
        self.screen.blit(text, text.get_rect(center=(self.screen.get_width() / 2, self.screen.get_height() / 2 - 40)))
        hint = self.fonts["body"].render("按 空格 / 回车 返回首页", True, self.colors["text_primary"])
        self.screen.blit(hint, hint.get_rect(center=(self.screen.get_width() / 2, self.screen.get_height() / 2 + 20)))
        if getattr(self, "exported_file", None):
            info = self.fonts["body"].render(f"已导出数据：{self.exported_file}", True, self.colors["text_primary"])
            self.screen.blit(info, info.get_rect(center=(self.screen.get_width() / 2, self.screen.get_height() / 2 + 70)))

    def _draw_question_panel(self) -> None:
        margin_x = int(80 * self.scale)
        panel_rect = pygame.Rect(
            margin_x,
            int(180 * self.scale),
            self.screen.get_width() - margin_x * 2,
            int(self.screen.get_height() * 0.45),
        )
        pygame.draw.rect(self.screen, self.colors["panel"], panel_rect, border_radius=16)
        pygame.draw.rect(self.screen, self.colors["accent"], panel_rect, width=2, border_radius=16)
        if not self.current_question_display:
            return
        font = self.fonts.get("question", self.fonts["body"])
        wrap_width = panel_rect.width - int(60 * self.scale)
        segments = self._current_question_segments or self._build_question_segments(
            self.current_question_display,
            self._current_question_highlight,
            wrap_width,
        )

        portrait_size = int(min(panel_rect.width, panel_rect.height) * 0.4)
        portrait_rect = pygame.Rect(0, 0, portrait_size, portrait_size)
        portrait_rect.center = (panel_rect.centerx, panel_rect.top + portrait_size // 2 + int(25 * self.scale))
        border_radius = max(12, int(18 * self.scale))
        if self.current_portrait_entry and self.current_portrait_entry.get("surface") is not None:
            surface = self.current_portrait_entry["surface"]
            if surface:
                if (
                    self._current_portrait_scaled is None
                    or self._current_portrait_scaled.get_size() != portrait_rect.size
                ):
                    self._current_portrait_scaled = pygame.transform.smoothscale(surface, portrait_rect.size)
                self.screen.blit(self._current_portrait_scaled, portrait_rect)
        else:
            pygame.draw.rect(self.screen, (214, 218, 230), portrait_rect, border_radius=border_radius)
        pygame.draw.rect(self.screen, self.colors["accent"], portrait_rect, width=3, border_radius=border_radius)

        if self.current_subject_name:
            name_surface = self.fonts["body"].render(self.current_subject_name, True, self.colors["text_primary"])
            name_rect = name_surface.get_rect(center=(portrait_rect.centerx, portrait_rect.bottom + int(18 * self.scale)))
            self.screen.blit(name_surface, name_rect)
            text_start_y = name_rect.bottom + int(36 * self.scale)
        else:
            text_start_y = portrait_rect.bottom + int(36 * self.scale)
        line_height = int(font.get_linesize() * 1.3)
        text_bottom = text_start_y
        for idx, (line, color) in enumerate(segments):
            surf = font.render(line, True, color)
            text_rect = surf.get_rect(center=(panel_rect.centerx, text_start_y + idx * line_height))
            self.screen.blit(surf, text_rect)
            text_bottom = text_rect.bottom

        info_font = self.fonts["body"]
        caption = info_font.render(
            f"第 {self.current_trial} 次 - 题目 {self.current_question_order}",
            True,
            self.colors["text_primary"],
        )
        min_caption_y = text_bottom + int(40 * self.scale)
        max_caption_y = panel_rect.bottom - int(60 * self.scale)
        caption_y = max(min_caption_y, min(max_caption_y, panel_rect.bottom - int(80 * self.scale)))
        caption_rect = caption.get_rect(center=(panel_rect.centerx, caption_y))
        self.screen.blit(caption, caption_rect)
        if self.current_question_order == 1 and self.mode == "practice":
            hint = info_font.render("完成评分后点击确认，准备进行第二次评分。", True, self.colors["text_primary"])
            hint_y = min(panel_rect.bottom - int(20 * self.scale), caption_rect.bottom + int(30 * self.scale))
            hint_rect = hint.get_rect(center=(panel_rect.centerx, hint_y))
            self.screen.blit(hint, hint_rect)

    def _wrap_text(self, text: str, max_width: int) -> Tuple[str, ...]:
        font = self.fonts.get("question", self.fonts["body"])
        lines = []
        buffer = ""
        max_width = max(100, max_width)
        for char in text:
            if char == "\n":
                lines.append(buffer)
                buffer = ""
                continue
            next_buffer = buffer + char
            if font.render(next_buffer, True, self.colors["text_primary"]).get_width() > max_width and buffer:
                lines.append(buffer)
                buffer = char
            else:
                buffer = next_buffer
        if buffer:
            lines.append(buffer)
        return tuple(lines)

    def _compose_question_display(self, text: str) -> str:
        symbol = self.current_symbol or self._category_symbol(self.current_category)
        prefix = f"[{symbol}] " if symbol else ""
        subject = self.current_subject_name
        body = f"{subject}{text}" if subject else text
        return f"{prefix}{body}"

    def _category_symbol(self, category: Optional[str]) -> str:
        if not category:
            return "~"
        if len(category) == 1:
            return category
        lowered = category.lower()
        if lowered == "none":
            return "~"
        if lowered.startswith("moral"):
            return "P"
        if lowered.startswith("immoral"):
            return "N"
        if lowered.startswith("amoral") or lowered.startswith("neutral"):
            return "A"
        return category[:1].upper()

    def _build_debug_lines(self) -> None:
        plan: List[str] = []
        if hasattr(self.stimuli, "get_rule_plan"):
            plan = self.stimuli.get_rule_plan()
        if not plan:
            self._debug_lines = (
                f"当前总试次：{self.total_trials}",
                "未启用拉丁方或未生成规则序列。",
            )
            return

        indices_by_rule: Dict[str, List[int]] = {}
        order: List[str] = []
        for idx, code in enumerate(plan, start=1):
            if code not in indices_by_rule:
                indices_by_rule[code] = []
                order.append(code)
            indices_by_rule[code].append(idx)

        independent = getattr(self.stimuli, "is_independent_mode", lambda: True)()
        lines: List[str] = [
            f"总试次：{len(plan)}",
            f"题目是否不重复：{'是' if independent else '否'}",
        ]
        symbol_defs = getattr(self.stimuli, "get_symbol_definitions", lambda: {})()
        if symbol_defs:
            lines.append("符号说明：")
            for symbol, desc in symbol_defs.items():
                lines.append(f"  {symbol}：{desc}")
        weight_info = getattr(self.stimuli, "get_rule_weights", lambda: [])()
        if weight_info:
            lines.append("目标概率：")
            for code, weight, specified in weight_info:
                pct = f"{weight * 100:.1f}%"
                if specified is not None:
                    lines.append(f"  {code}：{pct}（显式设为 {specified:.3f}）")
                else:
                    lines.append(f"  {code}：{pct}（自动分配）")
        lines.append("规则分配：")
        for code in order:
            positions = indices_by_rule[code]
            trial_str = "、".join(str(pos) for pos in positions)
            lines.append(f"  {code}：次数 {len(positions)} -> 试次 {trial_str}")
        self._debug_lines = tuple(lines)

    def _refresh_question_segments(self) -> None:
        if not self.current_question_display:
            self._current_question_segments = ()
            return
        margin_x = int(80 * self.scale)
        panel_width = self.screen.get_width() - margin_x * 2
        wrap_width = panel_width - int(60 * self.scale)
        self._current_question_segments = self._build_question_segments(
            self.current_question_display,
            self._current_question_highlight,
            wrap_width,
        )

    def _build_question_segments(
        self,
        text: str,
        highlight: Optional[str],
        wrap_width: int,
    ) -> Tuple[Tuple[str, Tuple[int, int, int]], ...]:
        segments: List[Tuple[str, Tuple[int, int, int]]] = []
        default_color = self.colors["text_primary"]
        highlight_color = self.colors["disabled"]
        highlight_line = highlight.strip() if highlight else None
        lines = text.split("\n") if "\n" in text else [text]
        for raw_line in lines:
            stripped = raw_line.strip()
            color = highlight_color if highlight_line and stripped == highlight_line else default_color
            wrapped = self._wrap_text(raw_line, wrap_width)
            if not wrapped:
                segments.append(("", color))
                continue
            for entry in wrapped:
                segments.append((entry, color))
        return tuple(segments)

    def _load_portraits(self) -> List[Dict[str, object]]:
        raw = getattr(self.config, "raw", {})
        pictures_setting = raw.get("pictures_dir", "pictures") if isinstance(raw, dict) else "pictures"
        base_dir = Path(getattr(self.config, "_path", "config.json")).parent
        pictures_path = Path(pictures_setting)
        if not pictures_path.is_absolute():
            pictures_path = base_dir / pictures_path
        if not pictures_path.exists() or not pictures_path.is_dir():
            raise ValueError(f"未找到画像目录: {pictures_path}")
        allowed_ext = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}
        portraits: List[Dict[str, object]] = []
        for file in sorted(pictures_path.iterdir()):
            if file.suffix.lower() not in allowed_ext:
                continue
            try:
                image = pygame.image.load(str(file)).convert_alpha()
            except pygame.error:
                continue
            name = file.stem
            portraits.append({"name": name, "surface": image})
        if not portraits:
            raise ValueError(f"画像目录 {pictures_path} 中未找到有效的图片")
        return portraits
