# Contributing

欢迎提 PR。本仓库只做一件事：把图片生成能力做成**可被 Agent 宿主直接加载的技能**，不引入服务端。

## 基本要求

1. **不引入服务端**：技能只能通过标准库 HTTP 调用外部 API，不允许加 MCP server、常驻进程、
   `pip` 运行时依赖或数据库。
2. **不落盘密钥**：只读进程环境变量；不解析 `.env`，不写 token 到文件，不在日志里打印 token。
3. **技能自包含**：脚本、参考文档都放在 `skills/<skill>/` 内，路径相对技能目录；
   跨技能调用写清「找不到就停下让用户补装」，不要静默降级。
4. **克制默认行为**：`tier=default` 链路是日常唯一默认，`tier=fallback` 只能显式点名或显式开关。
5. **不写价格**：仓库里不出现单价、计费方式、成本比较。技能只描述「转发到哪个中转站、
   按什么顺序回退」，计费由用户自己的网关账号决定。

## 技能约定

`skills/<name>/SKILL.md` 的 frontmatter 至少包含：

| 字段 | 要求 |
|------|------|
| `name` | 必须与目录名一致 |
| `description` | 说清「什么场景该用」，写触发条件而不是功能罗列 |
| `version` | 与仓库 `VERSION` 一致 |
| `license` | `MIT` |
| `platforms` | 支持的操作系统 |
| `prerequisites` | 可选：外部命令、必需环境变量 |
| `setup.help` | 可选：缺少依赖时 Agent 该怎么办 |

正文用中文，写**可执行流程**：先做什么、校验什么、失败怎么处理、什么情况必须停下问用户。

## 提交前自检

```bash
npx skills add ./ --list                     # 确认 skills CLI 能发现技能（可选）
python3 scripts/validate_skills.py          # frontmatter / 版本 / 语法 / 泄密 / 价格信息
python3 skills/img-gen/scripts/img_gen.py check        # 无 key 时应退出码 1 并提示缺变量
python3 skills/img-gen/scripts/img_gen.py generate --help
python3 skills/gpt-icon-generate/scripts/plan_icon_sheet_params.py --width 2048 --height 2048 --rows 4 --cols 4
```

CI 会跑同一批检查（`validate.yml`）。**不要**为了通过检查把真实 API key 或内网地址写进仓库。

## 新增 preset

1. 在 `skills/img-gen/scripts/lib/presets.py` 注册：`provider`、`models`、`base_url`、`tier`、
   `size_policy`、`qualities`、字段派发策略。
2. 在 `skills/img-gen/scripts/presets/{gpt,banana}/` 加同名薄封装脚本。
3. 更新 `skills/img-gen/references/presets.md`：`route`、`tier`、实测状态。
4. 若是协议层面的新事实（尺寸表、quality 档位、鉴权头），同步更新 `references/`。

## 发版流程

1. 改 `VERSION` 与两个 `SKILL.md` 的 `version`，保持一致（无额外清单文件需要同步）。
2. 在 `CHANGELOG.md` 顶部加一节（Added / Changed / Removed / Migration）。
3. `python3 scripts/validate_skills.py` 通过后提 PR。
4. 合并后在 GitHub 上打 tag `vX.Y.Z` 并发 Release，说明直接引用 CHANGELOG 对应小节。
