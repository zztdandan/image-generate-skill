# Changelog

本仓库遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 与 [语义化版本](https://semver.org/lang/zh-CN/)。
仓库版本记录在 [`VERSION`](./VERSION)，两个技能的 `SKILL.md` frontmatter `version` 与之同步，由 `scripts/validate_skills.py` 在 CI 中校验。

## [2.3.0] — 2026-10-27

**仓库定位重置（Breaking）：从「远程 MCP 图片服务」变为「纯技能集合」。**

这是一个新的项目起点：旧仓库 `image-generate-mcp-remote` 的 MCP 服务端代码、PyPI 发布链路、
systemd 部署文档与测试全部移除，只保留两个可直接被 Agent 宿主加载的技能。

技能只做一件事：**把生图请求转发到你配置的中转生图站**（OpenAI-Images / Gemini 兼容网关）。
仓库与技能文档里不记录任何单价、计费方式或成本比较——各站怎么结算，由你自己的网关账号决定。

### Added

- `skills/img-gen`：直接生图 / 改图技能
  - 23 个 preset（GPT-Image 2 / 2.5 × 20、Nano Banana 2 × 3），覆盖多家中转站与官方通道
  - `route` 元数据（`proxy` / `official_relay` / `official`）与 `tier` 链路分级
    （`default` / `standard` / `fallback`）
  - 30 档精确像素尺寸表 + 每 preset 的 `quality` 上限校验
  - `check` / `generate` / `edit` 三个子命令，`check_env.py` 单独可用
  - `references/` 三份参考：preset 清单、HTTP 协议、尺寸映射
- `skills/gpt-icon-generate`：图标板 → 透明 PNG 图标包技能
  - 尺寸校验、切图参数规划、connected-bbox 切图三个脚本
  - 生图全部委托给 `img-gen`（`../img-gen/scripts/img_gen.py`），不绑定任何具体工具名
- 安装形态对齐 skills CLI：仓库按 `skills/<name>/SKILL.md` 布局，`npx skills add zztdandan/image-generate-skill`
  即可发现并安装两个技能，无需任何清单文件
- `scripts/validate_skills.py`：校验 frontmatter / 版本 / 语法 / 泄密 / 价格信息，CI 工作流
  `validate.yml` 调用
- `VERSION`、`CHANGELOG.md`、`CONTRIBUTING.md`

### Changed

- 仓库命名为 `image-generate-skill`，README 改为技能分享形态（技能清单 / 安装 / 快速开始 / 线路模型）
- 线路语义取代原来的计费语义：
  - `tier`：`preferred` → `default`，`last_resort` → `fallback`
  - CLI：`--allow-expensive` → `--allow-fallback`
  - `DEFAULT_CHAIN` / `FALLBACK_CHAIN` 取代 `CHEAP_CHAIN` / `LAST_RESORT_CHAIN`
  - preset 元数据去掉全部计费 / 价格类字段，新增 `route`
  - `img-gen check` 打印 `tier` + `route`，不再打印价格
- `gpt-icon-generate` 的 MCP 工具名替换为 `img_gen.py` 调用；`right_codes` / 陌生站点改为
  preset 或一次性调用说明
- 技能内部路径改为相对技能目录（`scripts/...`），不再出现 `.opencode/skills/...` 硬编码
- 两个技能 license 从「Proprietary. Internal project skill.」改为 `MIT`，与仓库一致
- `gpt-icon-generate` 增加 `version: 2.3.0` 与 `prerequisites`（`python3`、`identify`、`convert`）
- 环境变量名（`IMG_GEN_*_OFFICIAL_*`）保持不变，避免破坏既有配置；文档标注为历史命名

### Removed

- `.claude-plugin/marketplace.json` 与 `plugin.json`：安装改走 skills CLI 自动发现，不再维护 Claude 插件清单
- `image_generate_mcp_remote/`（MCP server、preset class registry、临时探索工具、后台落盘）
- `tests/`、`pyproject.toml`、`uv.lock`、`.python-version`、`.env.example`
- PyPI 发布工作流与 `SYSTEMD_DEPLOYMENT_GUIDE.md`（不再有服务端可部署）
- `skills/img-gen/.skillhub/metadata.json`（内部 skillhub 注册信息，含内网地址）
- `AGENTS.md`（MCP 服务端 Python 类型规范，已不适用于技能仓库）
- 所有价格 / 计费类描述：单价表、计费方式、成本对比、按 token 计费的提示语

### Migration

| 旧用法（MCP） | 新用法（技能） |
|--------------|---------------|
| `mcp__image_generate_mcp_remote__gpt_image_2_official` | `python3 scripts/img_gen.py generate`（auto → 默认链路） |
| `mcp__image_generate_mcp_remote__nano_banana_2_official` | `python3 scripts/img_gen.py generate --preset laozhang_nano_banana_pro` |
| `..._list_image_tools_catalog_tool` / `..._list_image_presets_tool` | `python3 scripts/img_gen.py check` |
| MCP 客户端 `timeout: 500000` | CLI 默认 `--timeout 360`（同步接口，断开即丢结果，别随意调低） |
| 服务端 `.env` + systemd | 宿主启动时注入的进程环境变量 |

升级注意：脚本里若用到 `--allow-expensive`，改为 `--allow-fallback`。
