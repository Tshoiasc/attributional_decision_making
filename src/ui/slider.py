from typing import Tuple

import pygame


def _is_whole_number(value: float) -> bool:
    try:
        return float(value).is_integer()
    except (TypeError, ValueError):
        return False


class Slider:
    """滑动条组件，支持步长限制"""

    def __init__(
        self,
        start_pos: Tuple[int, int],
        length: int,
        min_value: float,
        max_value: float,
        step: float,
        font: pygame.font.Font,
        label_low: str,
        label_high: str,
        colors: Tuple[Tuple[int, int, int], Tuple[int, int, int], Tuple[int, int, int]],
        label_color: Tuple[int, int, int],
        scale: float = 1.0,
        label_medium: str = "",
    ) -> None:
        self.x, self.y = start_pos
        self.length = length
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.font = font
        self.label_low = label_low
        self.label_high = label_high
        self.label_medium = label_medium
        self.track_color, self.handle_color, self.disabled_color = colors
        self.label_color = label_color
        self.scale = max(scale, 0.5)
        self.enabled = False
        self.handle_radius = max(8, int(14 * self.scale))
        self.track_height = max(4, int(6 * self.scale))
        self.value = (min_value + max_value) / 2
        self._dragging = False

    def draw(self, surface: pygame.Surface) -> None:
        track_rect = pygame.Rect(self.x, self.y, self.length, self.track_height)
        track_color = self.track_color if self.enabled else self.disabled_color
        pygame.draw.rect(surface, track_color, track_rect, border_radius=4)

        handle_x = self._value_to_position(self.value)
        handle_color = self.handle_color if self.enabled else self.disabled_color
        pygame.draw.circle(surface, handle_color, (int(handle_x), self.y + self.track_height // 2), self.handle_radius)

        text_color = self.label_color if self.enabled else self.disabled_color
        scale_offset_y = int(45 * self.scale)
        
        # 绘制左侧和右侧标签
        low_label = self.font.render(self.label_low, True, text_color)
        high_label = self.font.render(self.label_high, True, text_color)
        surface.blit(low_label, (self.x - low_label.get_width() // 2, self.y + scale_offset_y))
        surface.blit(high_label, (self.x + self.length - high_label.get_width() // 2, self.y + scale_offset_y))
        
        # 绘制中间标签（如果有的话）
        if self.label_medium:
            medium_label = self.font.render(self.label_medium, True, text_color)
            medium_x = self.x + self.length // 2 - medium_label.get_width() // 2
            surface.blit(medium_label, (medium_x, self.y + scale_offset_y))

        value_offset = int(65 * self.scale)
        format_str = self._get_value_format()
        value_label = self.font.render(f"当前评分：{self.value:{format_str}}", True, text_color)
        surface.blit(value_label, (self.x + self.length // 2 - value_label.get_width() // 2, self.y - value_offset))

        if self.step > 0:
            tick_count = int(round((self.max_value - self.min_value) / self.step)) + 1
            tick_height = max(6, int(12 * self.scale))
            tick_thickness = max(1, int(2 * self.scale))
            tick_color = text_color
            
            # 绘制刻度线和数值标签
            for i in range(tick_count):
                tick_value = self.min_value + i * self.step
                tick_x = int(self._value_to_position(tick_value))
                
                # 绘制刻度线
                pygame.draw.line(
                    surface,
                    tick_color,
                    (tick_x, self.y),
                    (tick_x, self.y + tick_height),
                    tick_thickness,
                )
                
                # 绘制数值标签
                format_str = self._get_value_format()
                tick_label = self.font.render(f"{tick_value:{format_str}}", True, text_color)
                label_x = tick_x - tick_label.get_width() // 2
                label_y = self.y + tick_height + int(8 * self.scale)
                surface.blit(tick_label, (label_x, label_y))

    def handle_event(self, event: pygame.event.Event) -> None:
        if not self.enabled:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._is_on_handle(event.pos):
                self._dragging = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging = False
        elif event.type == pygame.MOUSEMOTION and self._dragging:
            self._update_from_position(event.pos[0])

    def _is_on_handle(self, pos: Tuple[int, int]) -> bool:
        handle_x = self._value_to_position(self.value)
        handle_y = self.y + self.track_height // 2
        return (pos[0] - handle_x) ** 2 + (pos[1] - handle_y) ** 2 <= self.handle_radius ** 2

    def _update_from_position(self, x: int) -> None:
        ratio = (x - self.x) / self.length
        ratio = max(0.0, min(1.0, ratio))
        raw_value = self.min_value + ratio * (self.max_value - self.min_value)
        snapped = round((raw_value - self.min_value) / self.step) * self.step + self.min_value
        snapped = max(self.min_value, min(self.max_value, snapped))
        self.value = snapped

    def _value_to_position(self, value: float) -> float:
        ratio = (value - self.min_value) / (self.max_value - self.min_value)
        return self.x + ratio * self.length

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        if not enabled:
            self._dragging = False

    def set_value(self, value: float) -> None:
        clamped = max(self.min_value, min(self.max_value, value))
        snapped = round((clamped - self.min_value) / self.step) * self.step + self.min_value
        snapped = max(self.min_value, min(self.max_value, snapped))
        self.value = snapped
        self._dragging = False

    def reset(self) -> None:
        self.value = (self.min_value + self.max_value) / 2
        self._dragging = False
        self.enabled = False

    def _get_value_format(self) -> str:
        """根据步长和值范围决定数值显示格式"""
        # 如果步长、最大值、最小值都是整数，使用g格式自动去掉小数点
        if (_is_whole_number(self.step) and
            _is_whole_number(self.min_value) and
            _is_whole_number(self.max_value)):
            return "g"
        # 否则根据步长的小数位数来显示
        else:
            # 计算步长的小数位数
            step_str = f"{float(self.step):.10f}".rstrip('0').rstrip('.')
            if '.' in step_str:
                decimal_places = len(step_str.split('.')[1])
                return f".{decimal_places}f"
            else:
                return ".2f"
