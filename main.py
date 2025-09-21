import sys
from datetime import datetime
from typing import Dict, Optional

import pygame

from src.config_loader import ConfigError, load_config
from src.recorder import DataRecorder
from src.scenes.experiment import ExperimentScene
from src.scenes.main_menu import MainMenuScene
from src.scenes.participant_form import ParticipantFormScene
from src.stimuli_manager import StimuliManager


def create_fonts(config, scale: float) -> Dict[str, pygame.font.Font]:
    pygame.font.init()
    fonts_conf = config.fonts
    font_path = getattr(config, "font_path", None)
    fallback_names = [
        "PingFang SC",
        "PingFangSC-Regular",
        "Microsoft YaHei",
        "MicrosoftYaHei",
        "SimHei",
        "WenQuanYi Zen Hei",
        "Noto Sans CJK SC",
        "Source Han Sans CN",
        "Songti SC",
    ]

    warning_issued = False

    def build(size: int) -> pygame.font.Font:
        nonlocal warning_issued
        target_size = max(12, int(round(size * scale)))
        if font_path:
            return pygame.font.Font(font_path, target_size)
        for name in fallback_names:
            matched = pygame.font.match_font(name, bold=False, italic=False)
            if matched:
                return pygame.font.Font(matched, target_size)
        if not warning_issued:
            print("警告：未找到可用的中文字体，请在 config.json 中配置 fonts.path，当前将使用默认字体。")
            warning_issued = True
        return pygame.font.Font(None, target_size)

    return {
        "title": build(fonts_conf.get("title_size", 48)),
        "subtitle": build(fonts_conf.get("subtitle_size", 32)),
        "body": build(fonts_conf.get("body_size", 24)),
        "question": build(fonts_conf.get("question_size", fonts_conf.get("body_size", 24))),
    }


def main() -> None:
    try:
        config = load_config()
    except ConfigError as exc:
        print(f"配置错误：{exc}")
        sys.exit(1)

    try:
        stimuli_manager = StimuliManager("stimuli.csv")
    except ValueError as exc:
        print(f"题库错误：{exc}")
        sys.exit(1)

    config.ensure_stimuli_capacity(stimuli_manager.total_questions)

    pygame.init()

    base_width = config.window.get("width", 1920)
    base_height = config.window.get("height", 1080)
    fullscreen = bool(config.window.get("fullscreen"))

    if fullscreen:
        display_info = pygame.display.Info()
        actual_width = display_info.current_w
        actual_height = display_info.current_h
        flags = pygame.FULLSCREEN
        screen = pygame.display.set_mode((actual_width, actual_height), flags)
    else:
        actual_width = base_width
        actual_height = base_height
        flags = 0
        screen = pygame.display.set_mode((actual_width, actual_height), flags)

    scale_x = actual_width / base_width if base_width else 1.0
    scale_y = actual_height / base_height if base_height else 1.0
    scale = min(scale_x, scale_y) if scale_x > 0 and scale_y > 0 else 1.0
    config.scale = scale
    config.screen_size = (actual_width, actual_height)
    pygame.display.set_caption(config.window.get("title", "心理学实验"))
    clock = pygame.time.Clock()

    fonts = create_fonts(config, scale)

    recorder: DataRecorder = DataRecorder(config.export_path("临时.csv"))
    participant_info: Optional[Dict[str, str]] = None

    current_scene = None
    state = "participant"

    def handle_info_submit(info: Dict[str, str]) -> None:
        nonlocal participant_info
        participant_info = info
        go_menu()

    def collect_participant(initial: bool = False) -> None:
        nonlocal current_scene, state
        state = "participant"
        current_scene = ParticipantFormScene(
            screen=screen,
            config=config,
            fonts=fonts,
            mode=None,
            on_submit=handle_info_submit,
            on_cancel=(lambda: None) if initial else go_menu,
            initial_values=participant_info,
            scale=scale,
        )

    def go_menu() -> None:
        nonlocal current_scene, state, recorder
        if participant_info is None:
            collect_participant(initial=True)
            return
        state = "menu"
        stimuli_manager.reset_session()
        recorder = DataRecorder(config.export_path("临时.csv"))
        recorder.set_participant_info(participant_info)
        current_scene = MainMenuScene(
            screen=screen,
            config=config.raw,
            fonts=fonts,
            on_select_mode=start_experiment,
            on_edit_info=lambda: collect_participant(initial=False),
            participant_info=participant_info,
            scale=scale,
        )

    def start_experiment(mode: str) -> None:
        nonlocal current_scene, state, recorder
        if participant_info is None:
            collect_participant(initial=True)
            return
        stimuli_manager.reset_session()
        if mode == "practice":
            export_name = config.experiment["practice_output"]
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prefix = config.experiment.get("formal_output_prefix", "formal_results")
            export_name = f"{prefix}_{timestamp}.csv"
        recorder = DataRecorder(config.export_path(export_name))
        recorder.set_participant_info(participant_info)
        state = "experiment"
        current_scene = ExperimentScene(
            screen=screen,
            config=config,
            fonts=fonts,
            stimuli=stimuli_manager,
            recorder=recorder,
            mode=mode,
            participant_info=participant_info.copy(),
            scale=scale,
            on_finish=go_menu,
        )

    collect_participant(initial=True)

    while True:
        dt = clock.tick(60) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if current_scene:
                current_scene.handle_event(event)
        if current_scene:
            current_scene.update(dt)
            current_scene.draw()
        pygame.display.flip()


if __name__ == "__main__":
    main()
