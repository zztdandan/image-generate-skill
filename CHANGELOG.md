# Changelog

本仓库遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 与 [语义化版本](https://semver.org/lang/zh-CN/)。
仓库版本记录在 [`VERSION`](./VERSION)，两个技能的 `SKILL.md` frontmatter `version` 与之同步，由 `scripts/validate_skills.py` 在 CI 中校验。

## [2.3.0] — 2026-10-27

**仓库定位重置（Breaking）：从「远程 MCP 图片服务」变为「纯技能集合」。**

这是一个新的项目起点：旧仓库 `image-generate-mcp-remote` 的 MCP 服务端代码、PyPI 发布链路、
systemd 部署文档与测试全部移除，只保留两个可直接被 Agent 宿主加载的技能。

### Added

- `skills/img-gen`：直接生图 / 改图技能
  - 23 个 preset（GPT-Image 2 / 2.5 × 20、Nano Banana 2 × 3），`--preset auto` 计费路由
  - `tier` 分级（`preferred` / `standard` / `last_resort`）与 `--allow-expensive` 显式开关
  - 30 档精确像素尺寸表 + 每 preset 的 `quality` 上限校验
  - `check` / `generate` / `edit` 三个子命令，`check_env.py` 单独可用
  - `references/` 三份参考：preset 清单、HTTP 协议、尺寸映射
- `skills/gpt-icon-generate`：图标板 → 透明 PNG 图标包技能
  - 尺寸校验、切图参数规划、connected-bbox 切图三个脚本
  - 生图全部委托给 `img-gen`（`../img-gen/scripts/img_gen.py`），不再绑定 MCP 工具名
- `.claude-plugin/marketplace.json` + `plugin.json`：支持 `/plugin marketplace add` 一键安装
- `scripts/validate_skills.py`：校验 frontmatter/版本/语法/泄密，CI 工作流 `validate.yml` 调用
- `VERSION`、`CHANGELOG.md`、`CONTRIBUTING.md`

### Changed

- 仓库命名为 `image-generate-skill`，README 改为技能分享形态（技能清单 / 安装 / 快速开始 / 成本模型）
- `gpt-icon-generate` 的 MCP 工具名替换为 `img_gen.py` 调用；`right_codes`/陌生站点改为 preset 或一次性调用说明
- 技能内部路径改为相对技能目录（`scripts/...`），不再出现 `.opencode/skills/...` 硬编码
- 两个技能 license 从「Proprietary. Internal project skill.」改为 `MIT`，与仓库一致
- `gpt-icon-generate` 增加 `version: 2.3.0` 与 `prerequisites`（`python3`、`identify`、`convert`）
- 环境变量名（`IMG_GEN_*_OFFICIAL_*`）保持不变，避免破坏既有配置；文档标注为历史命名

### Removed

- `image_generate_mcp_remote/`（MCP server、preset class registry、临时探索工具、后台落盘）
- `tests/`、`pyproject.toml`、`uv.lock`、`.python-version`、`.env.example`
- PyPI 发布工作流与 `SYSTEMD_DEPLOYMENT_GUIDE.md`（不再有服务端可部署）
- `skills/img-gen/.skillhub/metadata.json`（内部 skillhub 注册信息，含内网地址）
- `AGENTS.md`（MCP 服务端 Python 类型规范，已不适用于技能仓库）

### Migration

| 旧用法（MCP） | 新用法（技能） |
|--------------|---------------|
| `mcp__image_generate_mcp_remote__gpt_image_2_official` | `python3 scripts/img_gen.py generate`（auto → `$0.03` 路线） |
| `mcp__image_generate_mcp_remote__nano_banana_2_official` | `python3 scripts/img_gen.py generate --preset laozhang_nano_banana_pro` |
| `..._list_image_tools_catalog_tool` / `..._list_image_presets_tool` | `python3 scripts/img_gen.py check` |
| MCP 客户端 `timeout: 500000` | CLI 默认 `--timeout 360`（同步接口，断开仍计费，别随意调低） |
| 服务端 `.env` + systemd | 宿主启动时注入的进程环境变量 |
