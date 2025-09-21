from typing import Callable, Dict, List, Optional

import pygame

from src.ui.button import Button
from src.ui.text_input import TextInput


class ParticipantFormScene:
    """被试信息登记界面"""

    def __init__(
        self,
        screen: pygame.Surface,
        config,
        fonts: Dict[str, pygame.font.Font],
        mode: Optional[str],
        on_submit: Callable[[Dict[str, str]], None],
        on_cancel: Callable[[], None],
        initial_values: Optional[Dict[str, str]] = None,
        scale: float = 1.0,
    ) -> None:
        self.screen = screen
        self.config = config
        self.fonts = fonts
        self.mode = mode
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        self.initial_values = initial_values or {}
        self.scale = max(scale, 0.5)
        colors = config.colors

        width = screen.get_width()
        form_width = int(width * 0.6)
        self.form_left = (width - form_width) // 2
        self.top_offset = int(screen.get_height() * 0.22)
        self.row_height = max(72, int(96 * self.scale))
        input_height = max(48, int(60 * self.scale))
        self.label_offset = max(80, int(120 * self.scale))

        self.layout: List[Dict[str, object]] = []
        self.fields: List[Dict[str, object]] = []
        rows = [
            ("name", "姓名", "input", False, 20),
            ("age", "年龄", "input", True, 3),
            ("gender", "性别", "gender", False, 0),
            ("class", "班级", "input", False, 20),
        ]

        for index, (key, label, field_type, digits_only, max_len) in enumerate(rows):
            y = self.top_offset + index * self.row_height
            entry: Dict[str, object] = {"key": key, "label": label, "type": field_type, "y": y}
            if field_type == "input":
                rect = pygame.Rect(self.form_left, y, form_width, input_height)
                input_box = TextInput(
                    rect=rect,
                    font=self.fonts["body"],
                    placeholder=f"请输入{label}",
                    text_color=colors["text_primary"],
                    placeholder_color=(210, 210, 220),
                    border_color=(130, 130, 145),
                    active_border_color=colors["accent"],
                    background_color=colors["panel"],
                    max_length=max_len,
                    digits_only=digits_only,
                    scale=self.scale,
                )
                existing = self.initial_values.get(key, "")
                if existing:
                    input_box.value = existing
                entry["input"] = input_box
                self.fields.append(entry)
            else:
                option_width = max(120, int(160 * self.scale))
                spacing = max(20, int(30 * self.scale))
                start_x = self.form_left
                option_rects = []
                for idx_opt, value in enumerate(["女", "男"]):
                    rect = pygame.Rect(start_x + idx_opt * (option_width + spacing), y, option_width, input_height)
                    option_rects.append((value, rect))
                entry["options"] = option_rects
            self.layout.append(entry)

        self.active_index = 0 if self.fields else -1
        if self.fields:
            self.fields[0]["input"].set_active(True)  # type: ignore[index]
        self.gender_selection = self.initial_values.get("gender") if self.initial_values.get("gender") in {"女", "男"} else None
        self.error_message = ""

        button_width = max(200, int(240 * self.scale))
        button_height = max(48, int(58 * self.scale))
        button_rect = pygame.Rect(0, 0, button_width, button_height)
        button_rect.center = (self.screen.get_width() // 2, self.top_offset + len(rows) * self.row_height + int(90 * self.scale))
        self.submit_button = Button(
            rect=button_rect,
            text="保存信息",
            font=self.fonts["body"],
            bg_color=colors["accent"],
            text_color=colors["button_text"],
            disabled_color=colors["disabled"],
            on_click=self._submit,
            scale=self.scale,
        )

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.on_cancel()
                return
            if event.key == pygame.K_TAB and self.fields:
                self._focus_next()
                return
            if event.key == pygame.K_RETURN:
                if self.fields and self.fields_index_of("class") == self.active_index:
                    self._submit()
                else:
                    self._focus_next()
                return
            if self.active_index >= 0:
                self._active_input.handle_key(event)
        elif event.type == pygame.TEXTINPUT and self.active_index >= 0:
            self._active_input.handle_text(event.text)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for idx, field in enumerate(self.fields):
                input_box: TextInput = field["input"]  # type: ignore[index]
                if input_box.rect.collidepoint(event.pos):
                    self._set_active(idx)
                    break
            for entry in self.layout:
                if entry["type"] == "gender":  # type: ignore[index]
                    for value, rect in entry["options"]:  # type: ignore[index]
                        if rect.collidepoint(event.pos):
                            self.gender_selection = value
                            self.error_message = ""
                            return
        self.submit_button.handle_event(event)

    def update(self, _dt: float) -> None:
        pass

    def draw(self) -> None:
        colors = self.config.colors
        self.screen.fill(colors["background"])
        title = self.fonts["title"].render("被试信息登记", True, colors["text_primary"])
        self.screen.blit(title, title.get_rect(center=(self.screen.get_width() / 2, self.screen.get_height() * 0.16)))

        subtitle_text = "请准确填写以下信息后开始实验"
        subtitle = self.fonts["subtitle"].render(subtitle_text, True, colors["text_primary"])
        self.screen.blit(subtitle, subtitle.get_rect(center=(self.screen.get_width() / 2, self.screen.get_height() * 0.24)))

        mode_text = "待选择" if self.mode is None else ("模拟实验" if self.mode == "practice" else "正式实验")
        mode_label = self.fonts["body"].render(f"当前模式：{mode_text}", True, colors["text_primary"])
        self.screen.blit(
            mode_label,
            (int(self.screen.get_width() * 0.18), self.top_offset - int(60 * self.scale)),
        )

        label_font = self.fonts["body"]
        for entry in self.layout:
            label_surface = label_font.render(entry["label"], True, colors["text_primary"])  # type: ignore[index]
            y = entry["y"]  # type: ignore[index]
            self.screen.blit(label_surface, (self.form_left - self.label_offset, y + int(12 * self.scale)))
            if entry["type"] == "input":  # type: ignore[index]
                input_box: TextInput = entry["input"]  # type: ignore[index]
                input_box.draw(self.screen)
            else:
                for value, rect in entry["options"]:  # type: ignore[index]
                    selected = value == self.gender_selection
                    bg_color = colors["accent"] if selected else (220, 220, 230)
                    text_color = colors["button_text"] if selected else (40, 40, 48)
                    border_radius = max(8, int(16 * self.scale))
                    pygame.draw.rect(self.screen, bg_color, rect, border_radius=border_radius)
                    pygame.draw.rect(self.screen, colors["accent"], rect, width=2, border_radius=border_radius)
                    text_surface = label_font.render(value, True, text_color)
                    self.screen.blit(text_surface, text_surface.get_rect(center=rect.center))

        if self.error_message:
            error_surface = label_font.render(self.error_message, True, (220, 82, 82))
            self.screen.blit(error_surface, (self.submit_button.rect.left, self.submit_button.rect.bottom + int(18 * self.scale)))

        self.submit_button.draw(self.screen)

    @property
    def _active_input(self) -> TextInput:
        return self.fields[self.active_index]["input"]  # type: ignore[index]

    def _set_active(self, index: int) -> None:
        for idx, field in enumerate(self.fields):
            input_box: TextInput = field["input"]  # type: ignore[index]
            input_box.set_active(idx == index)
        self.active_index = index

    def _focus_next(self) -> None:
        if not self.fields:
            return
        next_index = (self.active_index + 1) % len(self.fields)
        self._set_active(next_index)

    def fields_index_of(self, key: str) -> int:
        for idx, field in enumerate(self.fields):
            if field["key"] == key:  # type: ignore[index]
                return idx
        return 0

    def _submit(self) -> None:
        values = {}
        for field in self.fields:
            key = field["key"]  # type: ignore[index]
            input_box: TextInput = field["input"]  # type: ignore[index]
            values[key] = input_box.get_value()
        if not values.get("name"):
            self.error_message = "姓名不能为空"
            self._set_active(self.fields_index_of("name"))
            return
        if not values.get("age"):
            self.error_message = "年龄不能为空"
            self._set_active(self.fields_index_of("age"))
            return
        if not values["age"].isdigit():
            self.error_message = "年龄请填写数字"
            self._set_active(self.fields_index_of("age"))
            return
        if not self.gender_selection:
            self.error_message = "请选择性别"
            return
        if not values.get("class"):
            self.error_message = "班级不能为空"
            self._set_active(self.fields_index_of("class"))
            return
        self.error_message = ""
        self.on_submit(
            {
                "name": values["name"],
                "age": values["age"],
                "gender": self.gender_selection,
                "class": values["class"],
            }
        )
