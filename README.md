# Minimal Product UI

面向 React/Next.js 的个人 UI 设计技能。先做好极简纯白与深色，再根据功能和体验微调。
不固定套模板，不堆首页说明，不为视觉效果重复引入组件库。

## 使用与维护

技能入口：[SKILL.md](skills/minimal-product-ui/SKILL.md)。在 Codex 中调用：

```text
$minimal-product-ui 检查当前 React 项目，用极简纯白和深色优化界面，保留现有功能与输入输出格式。
```

主要文件：

- `SKILL.md`：工作流程、默认原则和执行边界。
- `references/workflow.md`：每次 UI 工作先读的选型、源码证据、实现与验收流程。
- `references/frontend-brief.md`：用户提供的完整前端工程提示词与使用说明。
- `references/visual-baseline.md`：双主题、排版、空间和反馈基线。
- `references/patterns-and-components.md`：React 生态按需选型。
- `references/heroui.md`、`react-bits.md`：版本、集成与许可注意事项。
- `references/lessons-and-acceptance.md`：设计教训及验收情境。
- `references/source-policy.md`、`upstreams.json`：源码核验流程与锁定提交。

首次获取可使用 `git clone https://github.com/TimYuhong/minimal-product-ui.git`。
维护时先 `git pull --ff-only`，编辑技能及所需参考，校验后提交并 `git push`。
不要强推覆盖远端变更，也不要把账号凭证、项目私有配置或业务输出放入仓库。

## 安装

从仓库根目录，将 `skills/minimal-product-ui` 接入你自己的 Codex 技能目录。
以下命令通过环境变量或当前用户目录解析目标，不依赖维护者的磁盘路径。
已有同名技能时先核对来源，不直接覆盖。

Windows PowerShell：

```powershell
$repoRoot = (Resolve-Path .).Path
$skillsDir = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME 'skills' } else { Join-Path $env:USERPROFILE '.codex\skills' }
$skillLink = Join-Path $skillsDir 'minimal-product-ui'
if (Test-Path -LiteralPath $skillLink) { throw '目标已存在，请先检查其来源；不要直接覆盖。' }
New-Item -ItemType Directory -Path $skillsDir -Force | Out-Null
New-Item -ItemType Junction -Path $skillLink -Target (Join-Path $repoRoot 'skills\minimal-product-ui')
```

macOS / Linux：

```sh
skills_dir="${CODEX_HOME:-$HOME/.codex}/skills"
mkdir -p "$skills_dir"
test ! -e "$skills_dir/minimal-product-ui" && test ! -L "$skills_dir/minimal-product-ui" &&
  ln -s "$PWD/skills/minimal-product-ui" "$skills_dir/minimal-product-ui"
```

目录链接让已安装技能与 Git 仓库使用同一份源文件。不要移动仍被链接引用的克隆目录；
迁移前先检查并更新链接，而不是删除源文件。

## 下载真实 UI 源码

本技能不是“记住库名然后自由发挥”。开始采用组件前，必须读取匹配版本的真实源码、
类型、样式与许可，记录来源。Git 和 Python 3.10+ 可用后，在仓库根目录运行：

```sh
python skills/minimal-product-ui/scripts/ui_sources.py fetch
python skills/minimal-product-ui/scripts/ui_sources.py verify
```

这会补齐 `upstreams.json` 中的 **15 个来源**：shadcn/ui、Radix Primitives、HeroUI、React Bits、
Magic UI、Aceternity UI、Lucide、Morphicons、Motion、Tailwind CSS、react-resizable-panels、
dnd-kit、Zustand、TanStack Query、Recharts。
其中 14 个使用固定 commit 的 Git sparse checkout；Aceternity 使用官方公开注册表的逐文件 SHA-256 快照，
包含 114 个公开 `registry:ui` 条目的原 JSON 和实际提取源码，不下载 blocks 或付费 templates。
源码位于技能内的 `assets/upstream/<source-id>/`，保留来源与许可证据，不运行上游安装/构建脚本。
可以用 `--source heroui` 等参数限制操作范围。

下载目录由脚本相对技能位置解析，是 Git 忽略的独立上游 checkout，不混入本仓库提交。
公开的锁定清单与脚本使其他使用者可以按相同版本获取源码；校验检查 Git origin、HEAD、本地修改、
关键文件，或注册表原文哈希及全部提取源码。若注册表远端已经变化且缓存缺失，获取会失败，
需要维护者明确更新快照，不能保证上游永久保留旧内容。离线且未取得源码时不能冒称官方实现。

这些快照供源码核验，不意味着应安装开发分支依赖或升级现有项目。
项目采用其他版本时，应先获取与实际安装版本匹配的官方 tag/commit，并记录证据。
详细流程见 [source-policy.md](skills/minimal-product-ui/references/source-policy.md)。

使用组件前必须先读工作流和选型矩阵，再校验并查看对应实现，例如在技能目录执行：

```sh
python scripts/ui_sources.py inspect --source morphicons --file src/react/index.tsx
python scripts/ui_sources.py inspect --source aceternity-ui --component sidebar
```

下载的是参考源码，不是在业务项目安装 15 套依赖；当前项目需要哪个能力才选择哪个来源。

## 校验

Python 3.10+，校验依赖独立于 React 项目；可在仓库内使用虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -B scripts/validate_skill.py
.\.venv\Scripts\python.exe -B scripts/validate_repository.py
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

本地校验检查技能结构、YAML 元数据、内部引用、公开文件中的个人绝对路径与校验器回归用例。
结构校验不证明实际 UI 设计、浏览器行为或真实业务成功；行为验收见技能内的情境清单。

自动校验模板位于 `maintenance/validate-workflow.yml`，当前尚未启用 GitHub Actions。
需要具备工作流写入权限时，再将模板放到 `.github/workflows/validate.yml` 并提交。
维护技能本身不需要额外授予 OAuth `workflow` 权限。

## 第三方 UI 来源

React 组件可以按项目需要选择 shadcn/Radix、HeroUI，局部视觉组件可以选择 React Bits、
Magic UI、Aceternity UI；其他生态工具按技能中的适用条件使用。
上游源码会实际下载到独立 checkout，公开仓库保存其锁定记录、可复现获取脚本和使用约束，
不把第三方整库或演示站重新分发为本技能的一部分。当前只读核验无需创建额外 fork；
需要维护上游改动时，再按组件、版本、许可与维护目标创建独立 fork。
采用的源码应记录来源/版本/改动并保留适用声明，不能把别人的代码换上本仓库的许可。
尤其注意 React Bits 的 MIT + Commons Clause 附加限制、Aceternity 的逐项使用/再分发限制、
Lucide 的 ISC/Feather 衍生图标 MIT 声明，以及 HeroUI 不同版本和文件的许可核对。
查阅文档不需要额外注册 MCP 或安装第三方 skills。

## 更新注册表快照

仅在明确维护本技能时，在技能目录执行：

```sh
python scripts/ui_sources.py refresh-registry --source aceternity-ui
```

命令创建新快照并生成内容锁，不覆盖旧缓存；发布前仍需检查源码、依赖与许可变化。
Git 来源的更新也需要明确选择新 commit 并验证，普通项目使用不能自动追踪上游 HEAD。
