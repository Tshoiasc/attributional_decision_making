from typing import Tuple

import pygame


class TextInput:
    """简易文本输入框，用于收集被试信息"""

    def __init__(
        self,
        rect: pygame.Rect,
        font: pygame.font.Font,
        placeholder: str,
        text_color: Tuple[int, int, int],
        placeholder_color: Tuple[int, int, int],
        border_color: Tuple[int, int, int],
        active_border_color: Tuple[int, int, int],
        background_color: Tuple[int, int, int],
        max_length: int = 32,
        digits_only: bool = False,
        scale: float = 1.0,
    ) -> None:
        self.rect = rect
        self.font = font
        self.placeholder = placeholder
        self.text_color = text_color
        self.placeholder_color = placeholder_color
        self.border_color = border_color
        self.active_border_color = active_border_color
        self.background_color = background_color
        self.max_length = max_length
        self.digits_only = digits_only
        self.value = ""
        self.active = False
        self._caret_visible = True
        self._last_toggle = 0
        self._caret_interval = 400  # ms
        self.scale = max(scale, 0.5)
        self.border_radius = max(6, int(12 * self.scale))

    def set_active(self, active: bool) -> None:
        self.active = active
        if active:
            self._caret_visible = True
            self._last_toggle = pygame.time.get_ticks()

    def handle_key(self, event: pygame.event.Event) -> None:
        if not self.active:
            return
        if event.key == pygame.K_BACKSPACE:
            self.value = self.value[:-1]
            return
        if event.key in (pygame.K_RETURN, pygame.K_TAB):
            return

    def handle_text(self, text: str) -> None:
        if not self.active:
            return
        for char in text:
            if self.digits_only and not char.isdigit():
                continue
            if len(self.value) >= self.max_length:
                break
            self.value += char

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, self.background_color, self.rect, border_radius=self.border_radius)
        border_color = self.active_border_color if self.active else self.border_color
        pygame.draw.rect(surface, border_color, self.rect, width=2, border_radius=self.border_radius)

        display_text = self.value if self.value else self.placeholder
        color = self.text_color if self.value else self.placeholder_color
        text_surface = self.font.render(display_text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.midleft = (self.rect.left + 12, self.rect.centery)
        surface.blit(text_surface, text_rect)

        if self.active:
            now = pygame.time.get_ticks()
            if now - self._last_toggle >= self._caret_interval:
                self._caret_visible = not self._caret_visible
                self._last_toggle = now
            if self._caret_visible:
                caret_x = text_rect.right + 4
                caret_top = self.rect.top + int(10 * self.scale)
                caret_bottom = self.rect.bottom - int(10 * self.scale)
                pygame.draw.line(surface, self.text_color, (caret_x, caret_top), (caret_x, caret_bottom), 2)

    def get_value(self) -> str:
        return self.value.strip()

    def clear(self) -> None:
        self.value = ""
        self.active = False
