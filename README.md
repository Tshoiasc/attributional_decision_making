# 内在 vs 外在驱动心理学实验程序

该项目基于 Pygame 构建，用于模拟在改变主意场景下内在思考后验与外在证据的交互，包含模拟实验与正式实验两种流程，满足心理学实验常见的界面与数据记录需求。

## 环境依赖

- Python 3.9 及以上
- pygame

安装依赖：

```bash
pip install pygame
```

## 文件结构

- `main.py`：程序入口，负责场景切换与主循环
- `config.json`：实验核心配置（窗口、评分区间、时序等）
- `stimuli.csv`：题库文件，需包含 `moral` 与 `immoral` 两列
- `src/config_loader.py`：配置加载与合法性校验
- `src/stimuli_manager.py`：题库读取与随机调度
- `src/recorder.py`：数据记录与导出
- `src/ui/`：基础 UI 组件（按钮、滑动条）
- `src/scenes/`：场景定义（首页、实验流程）
- `data/`：默认结果导出目录

## 快速开始

```bash
python main.py
```

- 首页可选择「模拟实验」或「正式实验」
- 滑动条默认禁用，需要点击「开始评分」启用
- 完成评分后点击「确认」，按钮将置灰并记录数据
- 第一题确认后，系统会按照配置的概率和延迟选择性呈现第二题
- 右上角实时显示单题用时与总用时
- 每道题目对应的类别、评分、确认时间等信息将写入 `data/` 目录下的 CSV 文件

## 配置说明

`config.json` 中可配置以下内容：

- `window.fullscreen`：是否以全屏模式启动

- 程序启动时自动读取当前屏幕分辨率并按比例缩放字体、组件布局（默认设计尺寸来自 `window.width`/`height`）。
- `rating`：评分上下限、步长以及两端提示语
- `timing.second_question_probability`：第二题呈现概率
- `timing.second_question_delay_range`：第二题随机延迟范围（单位：秒）
- `timing.transition_duration`：试次之间的过渡时长
- `texts.home_subtitle`：首页副标题文案，可配置多行
- `display.show_timer` / `display.show_participant_info`：右上角计时与左上角被试信息是否展示
- `pictures_dir`：画像资源所在目录，程序会随机抽取其中的图片作为角色
- `fonts.path`：中文字体文件路径（留空则自动匹配系统常见字体）
- `fonts.title_size` / `subtitle_size` / `body_size` / `question_size`：标题、说明、正文字号以及题干字号
- `experiment.practice_trials` / `formal_trials`：模拟与正式试次数量（不得超过题目总量的一半）
- `experiment.export_directory`：结果导出目录
- `experiment.practice_output` / `formal_output_prefix`：数据文件名或前缀

## 题库扩展

- 在 `stimuli.csv` 中追加条目即可扩充题库
- 程序会自动确保同一运行过程中题目不重复
- 若正式试次数量超过题目总量的一半，程序会在启动时直接报错并退出

## 数据结构

导出的 CSV 字段：

- `participant_name` / `participant_age` / `participant_gender` / `participant_class`：被试基础信息
- `mode`：运行模式（practice/formal）
- `trial_index`：试次序号
- `q1_category` / `q1_stimulus` / `q1_rating_value` 等：第一题类别、文本、评分及时间轴字段（`_rating_started_at`、`_rating_confirmed_at`、`_elapsed_since_display`、`_trial_elapsed_total`）
- `q2_presented`：是否呈现第二题
- `q2_category` / `q2_stimulus` / `q2_rating_value` 等：第二题对应字段，若未呈现则为空

## 常见调整建议

1. **心理学动线**：可在 `ExperimentScene` 中调整过渡提示语或增加提示画面，保持被试注意力
2. **界面风格**：修改 `config.json` 中的颜色与字体参数即可快速调整整体视觉
3. **数据同步**：如需实时上传，可在 `DataRecorder` 中扩展导出逻辑，将记录发送至远程服务
4. **刺激分层**：若需要更多维度（例如情绪强度），可在 CSV 中添加额外列并在 `StimuliManager` 中扩展解析逻辑

## 注意事项

- 程序默认 60 FPS，如需调整请修改 `main.py` 中的 `clock.tick(60)`
- 为保证心理学实验的刺激独立性，请确保题目文本描述明确且彼此无重复语义
- 正式实验前建议使用「模拟实验」流程验证设备与配置

程序会在启动时根据屏幕分辨率缩放字体和布局，确保在 2880×1800 等高分辨率设备上保持良好显示。画像需命名为人物名字，例如 `小丁.png`，系统会在题干前自动加上 `{小丁}`。
