from typing import Callable, Dict, Optional

import pygame


class MainMenuScene:
    """实验首页场景"""

    def __init__(
        self,
        screen: pygame.Surface,
        config: Dict,
        fonts: Dict[str, pygame.font.Font],
        on_select_mode: Callable[[str], None],
        on_edit_info: Callable[[], None],
        participant_info: Optional[Dict[str, str]] = None,
        scale: float = 1.0,
    ) -> None:
        self.screen = screen
        self.config = config
        self.fonts = fonts
        self.on_select_mode = on_select_mode
        self.on_edit_info = on_edit_info
        self.participant_info = participant_info or {}
        self.scale = max(scale, 0.5)

        width = screen.get_width()
        height = screen.get_height()
        box_width = width * 0.25
        box_height = height * 0.15
        spacing = width * 0.1
        center_y = height * 0.6
        self.boxes = {
            "practice": pygame.Rect(
                int(width * 0.5 - spacing - box_width),
                int(center_y),
                int(box_width),
                int(box_height),
            ),
            "formal": pygame.Rect(
                int(width * 0.5 + spacing),
                int(center_y),
                int(box_width),
                int(box_height),
            ),
        }
        info_width = max(260, int(320 * self.scale))
        info_height = max(48, int(56 * self.scale))
        self.info_rect = pygame.Rect(0, 0, info_width, info_height)
        self.info_rect.center = (width // 2, int(height * 0.82))

    def draw(self) -> None:
        colors = self.config["colors"]
        self.screen.fill(colors["background"])
        title_font = self.fonts["title"]
        body_font = self.fonts["body"]

        title = title_font.render("内在思考与外在证据：决策驱动实验", True, colors["text_primary"])
        title_rect = title.get_rect(center=(self.screen.get_width() / 2, self.screen.get_height() * 0.25))
        self.screen.blit(title, title_rect)

        default_lines = [
            "通过模拟道德情境，探究改变主意时内在思考后验与外在证据的协同机制。",
            "请按照引导完成模拟或正式实验。",
        ]
        intro_lines = self.config.get("texts", {}).get("home_subtitle", default_lines)
        line_gap = int(body_font.get_linesize() * 1.4)
        for idx, line in enumerate(intro_lines):
            line_surf = body_font.render(line, True, colors["text_primary"])
            line_rect = line_surf.get_rect(
                center=(self.screen.get_width() / 2, self.screen.get_height() * 0.38 + idx * line_gap)
            )
            self.screen.blit(line_surf, line_rect)

        self._draw_participant_summary(colors, body_font)

        border_radius = max(12, int(16 * self.scale))
        for mode, rect in self.boxes.items():
            pygame.draw.rect(self.screen, colors["panel"], rect, border_radius=border_radius)
            pygame.draw.rect(self.screen, colors["accent"], rect, width=3, border_radius=border_radius)
            label = "模拟实验" if mode == "practice" else "正式实验"
            text_surface = body_font.render(label, True, colors["text_primary"])
            self.screen.blit(text_surface, text_surface.get_rect(center=rect.center))

        info_border_radius = max(16, int(20 * self.scale))
        pygame.draw.rect(self.screen, colors["panel"], self.info_rect, border_radius=info_border_radius)
        pygame.draw.rect(self.screen, colors["accent"], self.info_rect, width=2, border_radius=info_border_radius)
        info_text = body_font.render("重新登记被试信息", True, colors["text_primary"])
        self.screen.blit(info_text, info_text.get_rect(center=self.info_rect.center))

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for mode, rect in self.boxes.items():
                if rect.collidepoint(event.pos):
                    self.on_select_mode(mode)
                    return
            if self.info_rect.collidepoint(event.pos):
                self.on_edit_info()

    def update(self, _dt: float) -> None:
        pass

    def _draw_participant_summary(self, colors: Dict[str, int], font: pygame.font.Font) -> None:
        if not self.participant_info:
            return
        name = self.participant_info.get("name", "")
        age = self.participant_info.get("age", "")
        gender = self.participant_info.get("gender", "")
        klass = self.participant_info.get("class", "")
        summary_lines = [
            f"被试：{name}",
            f"年龄：{age}    性别：{gender}    班级：{klass}",
        ]
        line_gap = int(font.get_linesize() * 1.3)
        if not summary_lines:
            return
        button_top = min(rect.top for rect in self.boxes.values())
        total_height = line_gap * len(summary_lines)
        base_y = min(self.screen.get_height() * 0.5, button_top - total_height - int(30 * self.scale))
        base_y = max(int(self.screen.get_height() * 0.34), base_y)
        left_margin = int(self.screen.get_width() * 0.18)
        for idx, text in enumerate(summary_lines):
            surface = font.render(text, True, colors["text_primary"])
            self.screen.blit(surface, (left_margin, base_y + idx * line_gap))
