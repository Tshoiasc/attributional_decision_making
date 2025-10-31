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
- `timing.question_delay_range`：题目之间的随机间隔范围（单位：秒，对所有题目生效）
- `timing.transition_duration`：试次之间的过渡时长
- `question_controls.defaults` / `question_controls.overrides`：针对不同题目条件控制评分条等界面元素是否显示
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
- `question_order`：当前题目在试次中的顺序（从 1 开始）
- `rule_code`：拉丁方规则编码（若启用）
- `symbol`：题目符号（如 P/N/~/moral/immoral）
- `category`：题目所属类别
- `stimulus`：题干原文
- `rating_value` / `rating_started_at` / `rating_confirmed_at` / `elapsed_since_display` / `trial_elapsed_total`：评分结果与时间轴信息，若题目未展示评分条则评分字段为空
- `controls`：题目呈现时应用的控制参数（JSON 字符串），便于追溯界面配置

## 常见调整建议

1. **心理学动线**：可在 `ExperimentScene` 中调整过渡提示语或增加提示画面，保持被试注意力
2. **界面风格**：修改 `config.json` 中的颜色与字体参数即可快速调整整体视觉
3. **数据同步**：如需实时上传，可在 `DataRecorder` 中扩展导出逻辑，将记录发送至远程服务
4. **刺激分层**：若需要更多维度（例如情绪强度），可在 CSV 中添加额外列并在 `StimuliManager` 中扩展解析逻辑

## 注意事项

- 程序默认 60 FPS，如需调整请修改 `main.py` 中的 `clock.tick(60)`
- 为保证心理学实验的刺激独立性，请确保题目文本描述明确且彼此无重复语义
- 正式实验前建议使用「模拟实验」流程验证设备与配置
- 程序会在启动时根据屏幕分辨率缩放字体和布局，确保在 2880×1800 等高分辨率设备上保持良好显示。画像需命名为人物名字，例如 `小丁.png`，系统会在题干前自动加上 `{小丁}`。

## 打包与发布

### 本地打包

1. 安装依赖：

   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   pip install pyinstaller==6.9.0 pyinstaller-hooks-contrib==2024.7
   ```

2. 运行 PyInstaller：

   ```bash
   pyinstaller start_experiment.spec --noconfirm --clean
   ```

   - Windows：生成的可执行文件位于 `dist/PsychExperiment/PsychExperiment.exe`，可以进一步压缩成 ZIP。
   - macOS：生成 `dist/PsychExperiment.app`，可通过 `hdiutil create -ov -fs HFS+ -volname PsychExperiment -srcfolder dist/PsychExperiment.app dist/PsychExperiment.dmg` 制作 DMG。

> **提示**：PyInstaller 需要在目标平台上构建（Windows 打包 Windows，macOS 打包 macOS）。

### GitHub Actions 自动构建

仓库新增 `.github/workflows/build.yml`，在 `main` 分支 Push、PR 或手动触发时，会在 Windows 与 macOS 上运行打包流程，并上传对应的 ZIP/DMG 构建产物。

## 资源与数据存放策略

- `config.json`、`stimuli.csv`、`pictures/` 等资源默认与可执行文件放在同级目录；
- 运行时始终优先读取同级目录的配置与资源，若不存在再回退到内置默认值；
- 可直接修改同级目录的 `config.json`、`stimuli.csv` 或替换 `pictures/` 内容，无需重新打包；
- 结果文件默认写入配置中的 `data/` 目录；若该目录不可写（例如 macOS 应用放在 `/Applications` 中），程序会自动降级到用户目录：
  - Windows：`%APPDATA%/PsychExperiment/data`
  - macOS：`~/Library/Application Support/PsychExperiment/data`
  - Linux：`~/.local/share/PsychExperiment/data`
- `data/` 下的内容只是运行结果，不建议提交到版本库；仓库中保留了一个空的 `.gitkeep` 以维持目录结构。
- 如果需要将资源放在外置目录，可在 `config.json` 中将相关路径改为绝对路径，程序会按新的路径加载。
