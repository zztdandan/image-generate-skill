# image-generate-skill

> 一个 [Agent Skills](https://agentskills.io) 仓库，两个开箱即用的技能：**`img-gen`** 负责生图 / 改图（把请求转发到各类中转生图站），
> **`gpt-icon-generate`** 负责「图标板 → 校验 → 透明 PNG 图标包」。
> 纯 Python 标准库 + 原生 HTTP 调用，**不需要 MCP 服务、不需要 SDK、不需要 pip install**。

```bash
npx skills add zztdandan/image-generate-skill    # 装到当前项目
npx skills add zztdandan/image-generate-skill -g # 或装到用户级
```

[![release](https://img.shields.io/github/v/release/zztdandan/image-generate-skill?label=release)](https://github.com/zztdandan/image-generate-skill/releases)
[![license](https://img.shields.io/github/license/zztdandan/image-generate-skill)](./LICENSE)
[![python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![Agent Skill](https://img.shields.io/badge/agent%20skill-SKILL.md-6f42c1.svg)](./skills/img-gen/SKILL.md)
[![install](https://img.shields.io/badge/install-npx%20skills%20add-2ea44f.svg)](#安装)
[![validate](https://github.com/zztdandan/image-generate-skill/actions/workflows/validate.yml/badge.svg)](https://github.com/zztdandan/image-generate-skill/actions/workflows/validate.yml)

[English](#english) · [技能清单](#技能清单) · [安装](#安装) · [快速开始](#快速开始) · [线路模型](#线路模型) · [变更记录](./CHANGELOG.md)

---

## 技能清单

| 技能 | 干什么 | 依赖 |
|------|--------|------|
| [`img-gen`](./skills/img-gen/SKILL.md) | 文生图 / 图生图。把请求转发到各类中转生图站（GPT-Image 2.5、Nano Banana 2 等 OpenAI-Images / Gemini 兼容网关），共 23 个 preset、30 档精确尺寸、`--preset auto` 按默认链路自动回退 | `python3`（仅标准库） |
| [`gpt-icon-generate`](./skills/gpt-icon-generate/SKILL.md) | 规则网格图标板生成 → 尺寸校验 → 参数规划 → connected-bbox 切图 → 透明 PNG 图标包 / UI 图标库 | `python3` + ImageMagick（`identify` / `convert`）+ `img-gen` |

两个技能是**兄弟目录**：`gpt-icon-generate` 通过 `../img-gen/scripts/img_gen.py` 调用生图能力，所以安装时一起装。

## 安装

### 方式一：`npx skills`（推荐）

仓库按 skills CLI 的约定布局（`skills/<name>/SKILL.md`），无需任何清单文件：

```bash
# 装到当前项目（会生成 skills-lock.json，团队可复现）
npx skills add zztdandan/image-generate-skill

# 装到用户级，任何项目可用
npx skills add zztdandan/image-generate-skill -g

# 装两个技能到所有检测到的宿主，全程无交互
npx skills add zztdandan/image-generate-skill --skill '*' -a '*' -y

# 只装其中一个
npx skills add zztdandan/image-generate-skill --skill img-gen

# 先看看仓库里有什么（不安装）
npx skills add zztdandan/image-generate-skill --list
```

装完可用 `npx skills list` 查看、`npx skills update` 升级、`npx skills remove` 卸载。

> **两个技能建议一起装**：`gpt-icon-generate` 通过 `../img-gen/scripts/img_gen.py` 调用生图，
> 依赖两者位于同一个 skills 根目录（`npx skills` 装多个技能时天然同级）。

### 方式二：手动放到宿主的 skills 目录

```bash
git clone https://github.com/zztdandan/image-generate-skill.git
cd image-generate-skill

# 以 Claude Code 用户级目录为例，两个技能必须同级
mkdir -p ~/.claude/skills
ln -s "$PWD/skills/img-gen"            ~/.claude/skills/img-gen
ln -s "$PWD/skills/gpt-icon-generate"  ~/.claude/skills/gpt-icon-generate
```

不想用软链就 `cp -R skills/img-gen skills/gpt-icon-generate <skills-root>/`。

| 你的 Agent | skills 根目录（示例） |
|---|---|
| Claude Code | `<project>/.claude/skills/` 或 `~/.claude/skills/` |
| GitHub Copilot | `<project>/.github/skills/` |
| 通用 Agent Skills 宿主 | `~/.agents/skills/` 或该宿主文档指定的目录 |

最终形状必须是：

```text
<skills-root>/
├── img-gen/
│   ├── SKILL.md
│   ├── references/
│   └── scripts/
└── gpt-icon-generate/
    ├── SKILL.md
    └── scripts/
```

## 快速开始

### 1. 配置（只读进程环境变量）

技能**不读 `.env` 文件**，只认进程环境变量。在启动宿主之前注入：

```bash
export IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY=sk-...        # GPT 路线（推荐主力）
export IMG_GEN_GPT_IMAGE_2_OFFICIAL_PRESET=apiyi_gpt_image_2_5_vip
export IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY=sk-...      # Nano Banana 路线（可选）
export IMG_GEN_NANO_BANANA_2_OFFICIAL_PRESET=apiyi_nano_banana_2
export IMAGE_OUTPUT_DIR=$HOME/images                      # 可选，默认 ~/images
```

- 两个 key **至少有一个**；都没有时 `img-gen` 会直接停下并提示缺哪个变量，不会猜 key。
- 变量名里的 `OFFICIAL` 是历史命名（沿用旧 MCP 服务时代的变量），与「官方 API」无关，保留只为兼容既有配置。
- key 走任意 OpenAI Images 兼容网关（apiyi / laozhang / right.codes / copperai 等）或 Google Gemini；
  具体线路见 [`skills/img-gen/references/presets.md`](./skills/img-gen/references/presets.md)。

### 2. 生图 / 改图

```bash
cd <skills-root>/img-gen

# 环境自检：打印 key 状态、auto 链路、各 preset 的 route/tier（不打印 token）
python3 scripts/img_gen.py check

# 文生图（默认 --preset auto，只走 tier=default 的默认链路）
python3 scripts/img_gen.py generate \
  --prompt "A futuristic steel plant at dusk" \
  --save out.png --size 2K --ratio 16:9

# 精确像素 + 透明底图标
python3 scripts/img_gen.py generate \
  --prompt "linear icon of a sensor, flat, single object" \
  --save icon.png --size 1K --ratio 1:1 --background transparent --output-format png

# 改图（编辑 2K 成品要显式给尺寸）
python3 scripts/img_gen.py edit \
  --image input.png --prompt "Add a blue sky" \
  --save edited.png --size 2048x1152
```

### 3. 图标包（图标板 → 透明 PNG）

```bash
cd <skills-root>/gpt-icon-generate
IMG_GEN=../img-gen/scripts/img_gen.py

# 1) 生成 2K / 1:1 / 4x4 白底图标板
python3 "$IMG_GEN" generate --save /abs/path/app-sheet.png \
  --size 2K --ratio 1:1 --prompt "Create a premium icon sheet with exactly 16 distinct icons ..."

# 2) 校验实际尺寸（比例不符就重生成）
python3 scripts/verify_image_output.py /abs/path/app-sheet.png \
  --requested-width 2048 --requested-height 2048

# 3) 规划切图参数
python3 scripts/plan_icon_sheet_params.py --width 2048 --height 2048 --rows 4 --cols 4

# 4) 连通域切图 → 透明 PNG
python3 scripts/split_icon_sheet_connected_bbox.py /abs/path/app-sheet.png \
  /abs/path/app-icons --rows 4 --cols 4 --pad 18 --border 10 --fuzz 1.5%
```

完整提示词模板、切图算法、调参见 [`skills/gpt-icon-generate/SKILL.md`](./skills/gpt-icon-generate/SKILL.md)。

## 线路模型

`img-gen` 是**中转站转发器**：它不关心也不描述各站怎么算账，只编码「请求打到哪个站、
按什么顺序回退」。计费与额度请以你自己的网关账号为准。

| 维度 | 取值 | 含义 |
|------|------|------|
| `route` | `proxy` | 中转站 / 聚合站（多数 preset） |
| | `official_relay` | 官转通道（请求被转给官方 API） |
| | `official` | 官方 API 直连 |
| `tier` | `default` | 日常默认链路，`--preset auto` 按顺序走 |
| | `standard` | 备用 / 实验线路，需显式点名 |
| | `fallback` | 官方 / 官转线路，需 `--allow-fallback` 或显式点名 |

默认链路顺序：`apiyi_gpt_image_2_5_vip → apiyi_..._flare_vip → laozhang_..._sunburst_vip → laozhang_..._flare_vip`。
只有 401/403/404/408/409/425/429/5xx 与网络超时才跳下一条；HTTP 400（参数错误）立即停止，因为换线路也会一样失败。

## 目录结构

```text
image-generate-skill/
├── .github/workflows/validate.yml
├── scripts/validate_skills.py    # 发布前校验：frontmatter / 版本 / 语法 / 泄密 / 价格信息
├── skills/
│   ├── img-gen/
│   │   ├── SKILL.md
│   │   ├── references/{presets,protocols,size-mapping}.md
│   │   └── scripts/{img_gen,check_env}.py, lib/, presets/{gpt,banana}/
│   └── gpt-icon-generate/
│       ├── SKILL.md
│       └── scripts/{verify_image_output,plan_icon_sheet_params,split_icon_sheet_connected_bbox}.py
├── CHANGELOG.md
├── CONTRIBUTING.md
├── VERSION
└── LICENSE
```

## 技能规范

仓库布局按 [skills CLI](https://github.com/vercel-labs/skills) 的约定：技能放在
`skills/<name>/SKILL.md`，根目录**不放** `SKILL.md`（根级 `SKILL.md` 会短路发现流程），
也不需要任何清单文件——CLI 会自动发现。

每个技能目录必须包含 `SKILL.md`，frontmatter 至少声明：

```yaml
---
name: img-gen              # 必须与目录名一致
description: "..."         # 一句话说什么场景触发它
version: 2.3.0             # 与仓库 VERSION 同步
license: MIT
platforms: [linux, macos, windows]
---
```

其中 `prerequisites` / `setup` / `metadata` 为可选增强字段（声明外部命令、环境变量、
缺失时该怎么做）。提交前跑一次校验：

```bash
python3 scripts/validate_skills.py
```

CI 会在 push / PR 时自动执行同一份校验，并对 `img-gen` CLI 做无 key 冒烟测试。

## 依赖

- **`img-gen`**：Python 3.9+，仅标准库（`urllib` / `json` / `base64`），无需 `pip install`。
- **`gpt-icon-generate`**：同上，外加 ImageMagick（`identify`、`convert`）。
- **安装用**：`npx skills` 需要 Node.js 18+；技能运行本身不依赖 Node。

## 版本与变更

当前版本 **v2.3.0**：仓库从「MCP 图片服务」重构为「纯技能集合」，安装方式统一为
`npx skills add`，完整变更见 [CHANGELOG.md](./CHANGELOG.md)。

## English

An [Agent Skills](https://agentskills.io) collection with two skills. No MCP server, no SDK,
no pip install — plain Python stdlib HTTP calls.

- **`img-gen`** — text-to-image and image editing by forwarding requests to OpenAI-Images / Gemini
  compatible relay sites (GPT-Image 2.5, Nano Banana 2). 23 presets, 30 exact pixel slots,
  ordered default chain with automatic fallback. It does not describe or assume any billing —
  that belongs to whichever gateway your key points at.
- **`gpt-icon-generate`** — builds a regular-grid icon sheet (default 2K, 1:1, 4x4, white page),
  verifies the real output size, then splits it with connected-component bounding boxes into
  transparent PNGs for icon packs.

**Install with the skills CLI:**

```bash
npx skills add zztdandan/image-generate-skill        # current project
npx skills add zztdandan/image-generate-skill -g     # user-level
npx skills add zztdandan/image-generate-skill --list # browse without installing
```

**Or clone and link** both skill directories into your agent's skills root
(e.g. `~/.claude/skills/`, `~/.agents/skills/`). Keep them side by side: `gpt-icon-generate`
calls `../img-gen/scripts/img_gen.py`.

**Configure** via process environment only (no `.env` parsing):

```bash
export IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY=sk-...     # at least one key
export IMG_GEN_GPT_IMAGE_2_OFFICIAL_PRESET=apiyi_gpt_image_2_5_vip
export IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY=sk-...   # optional
```

```bash
python3 skills/img-gen/scripts/img_gen.py check
python3 skills/img-gen/scripts/img_gen.py generate --prompt "A futuristic steel plant" --save out.png
```

MIT licensed. Verify with `python3 scripts/validate_skills.py`.

## 许可证

[MIT](./LICENSE)
