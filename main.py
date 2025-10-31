import json
import os
import platform
import re
import sys
import subprocess
from datetime import datetime
from typing import Dict, Optional

import pygame

from src.config_loader import ConfigError, load_config
from src.recorder import DataRecorder
from src.scenes.experiment import ExperimentScene
from src.scenes.main_menu import MainMenuScene
from src.scenes.participant_form import ParticipantFormScene
from src.stimuli_manager import StimuliManager
from src.utils.paths import resource_path, runtime_file


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


def sanitize_for_filename(text: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "_", text.strip()) if text else ""
    cleaned = cleaned.strip("_")
    return cleaned or "Participant"


def load_participant_info_from_file() -> Optional[Dict[str, str]]:
    """从临时文件加载被试信息"""
    temp_file = runtime_file("temp_participant_info.json")
    if os.path.exists(temp_file):
        try:
            with open(temp_file, "r", encoding="utf-8") as f:
                info = json.load(f)
            # 删除临时文件
            os.remove(temp_file)
            print("已从临时文件加载被试信息:", info)
            return info
        except Exception as e:
            print(f"加载被试信息文件时出错: {e}")
    return None


def main() -> None:
    # 检查命令行参数
    skip_participant_form = "--skip-participant-form" in sys.argv
    
    try:
        config = load_config()
    except ConfigError as exc:
        print(f"配置错误：{exc}")
        sys.exit(1)

    try:
        stimuli_manager = StimuliManager(resource_path("stimuli.csv"), config)
    except ValueError as exc:
        print(f"题库错误：{exc}")
        sys.exit(1)

    try:
        config.ensure_stimuli_capacity(stimuli_manager)
    except ValueError as exc:
        print(f"题库错误：{exc}")
        sys.exit(1)

    pygame.init()

    # Windows输入法支持：启动ctfmon.exe
    is_windows = platform.system() == "Windows"
    is_mac = platform.system() == "Darwin"
    
    if is_windows:
        try:
            # 启动Windows输入法服务
            subprocess.Popen(["ctfmon.exe"], shell=True)
            print("已启动Windows输入法服务 (ctfmon.exe)")
        except Exception as e:
            print(f"启动输入法服务时出现警告: {e}")

    base_width = config.window.get("width", 1920)
    base_height = config.window.get("height", 1080)
    fullscreen = bool(config.window.get("fullscreen"))
    windows_ime_fix = bool(config.window.get("windows_ime_fix", True))
    mac_fullscreen_fix = bool(config.window.get("mac_fullscreen_fix", True))

    if fullscreen:
        display_info = pygame.display.Info()
        actual_width = display_info.current_w
        actual_height = display_info.current_h

        # Windows: 尝试多种模式来支持输入法
        if is_windows and windows_ime_fix:
            # 优先尝试SCALED模式（伪全屏但支持系统UI）
            try:
                os.environ['SDL_VIDEODRIVER'] = 'windows'
                flags = pygame.SCALED | pygame.RESIZABLE
                screen = pygame.display.set_mode((actual_width, actual_height), flags)
                print("Windows系统：使用SCALED伪全屏模式以支持输入法显示")
                print("提示：按Alt+Tab可切换窗口，Esc键退出程序")
            except Exception as e:
                print(f"SCALED模式失败，回退到NOFRAME模式: {e}")
                flags = pygame.NOFRAME
                screen = pygame.display.set_mode((actual_width, actual_height), flags)
                print("Windows系统：使用NOFRAME无边框模式")
            print("如需禁用此兼容模式，请在config.json中设置\"windows_ime_fix\": false")
        elif is_mac and mac_fullscreen_fix:
            flags = pygame.NOFRAME
            screen = pygame.display.set_mode((actual_width, actual_height), flags)
            print("macOS系统检测到，已使用无边框全屏模式以获得更好的兼容性")
            print("如需禁用此兼容模式，请在config.json中设置\"mac_fullscreen_fix\": false")
        else:
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
    
    # 尝试从文件加载被试信息（如果是通过独立窗口启动）
    participant_info: Optional[Dict[str, str]] = None
    if skip_participant_form:
        participant_info = load_participant_info_from_file()
        if not participant_info:
            print("错误：启动时指定跳过被试信息录入，但未找到被试信息文件")
            sys.exit(1)

    current_scene = None
    state = "participant"

    def handle_info_submit(info: Dict[str, str]) -> None:
        nonlocal participant_info
        participant_info = info
        go_menu()

    def collect_participant(initial: bool = False) -> None:
        nonlocal current_scene, state
        # 如果跳过被试信息录入且已有信息，直接进入主菜单
        if skip_participant_form and participant_info:
            go_menu()
            return
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
        safe_name = sanitize_for_filename(participant_info.get("name", ""))
        if mode == "practice":
            total_trials = stimuli_manager.practice_trial_count()
        else:
            total_trials = config.experiment["formal_trials"]
        stimuli_manager.begin_run(mode, total_trials)
        if mode == "practice":
            base_name = config.experiment["practice_output"]
            directory, filename = os.path.split(base_name)
            stem, ext = os.path.splitext(filename)
            if not stem:
                stem = "practice_results"
            ext = ext or ".csv"
            export_filename = f"{safe_name}_{stem}{ext}"
            export_name = os.path.join(directory, export_filename) if directory else export_filename
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prefix = config.experiment.get("formal_output_prefix", "formal_results")
            directory, base_prefix = os.path.split(prefix)
            if not base_prefix:
                base_prefix = "formal_results"
            export_filename = f"{safe_name}_{base_prefix}_{timestamp}.csv"
            export_name = os.path.join(directory, export_filename) if directory else export_filename
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
            total_trials_override=total_trials,
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
