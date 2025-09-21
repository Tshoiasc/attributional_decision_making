from typing import Callable, Tuple

import pygame


class Button:
    """基础按钮组件"""

    def __init__(
        self,
        rect: pygame.Rect,
        text: str,
        font: pygame.font.Font,
        bg_color: Tuple[int, int, int],
        text_color: Tuple[int, int, int],
        disabled_color: Tuple[int, int, int],
        on_click: Callable[[], None],
        scale: float = 1.0,
    ) -> None:
        self.rect = rect
        self.text = text
        self.font = font
        self.bg_color = bg_color
        self.text_color = text_color
        self.disabled_color = disabled_color
        self.on_click = on_click
        self.enabled = True
        self.border_radius = max(6, int(10 * max(scale, 0.5)))

    def draw(self, surface: pygame.Surface) -> None:
        color = self.bg_color if self.enabled else self.disabled_color
        pygame.draw.rect(surface, color, self.rect, border_radius=self.border_radius)
        label = self.font.render(self.text, True, self.text_color)
        text_rect = label.get_rect(center=self.rect.center)
        surface.blit(label, text_rect)

    def handle_event(self, event: pygame.event.Event) -> None:
        if not self.enabled:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.on_click()

    def set_enabled(self, value: bool) -> None:
        self.enabled = value
