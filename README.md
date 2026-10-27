# Minimal Product UI

面向 React/Next.js 的产品 UI 工作流：从界面问题出发，主动发现和比较成熟组件，
根据产品定位、既有设计语言与用户需求改善层次和交互，再检查实际页面质量。
保持简洁、现代与可维护；极简纯白/深色是可选基线，不是所有项目的固定风格。
局部任务走快路径；整体改造先明确布局取舍与验收场景，按正确完成任务的整体成本评价效率。

## 使用与维护

技能入口：[SKILL.md](skills/minimal-product-ui/SKILL.md)。在 Codex 中调用：

```text
$minimal-product-ui 检查当前 React 项目的层次与交互，沿用产品设计语言，主动评估成熟组件并验证页面质量，保留现有功能与输入输出格式。
```

主要文件：

- `SKILL.md`：能力入口、参考路由和执行边界。
- `references/workflow.md`：局部快路径与整体设计流程，串联任务基线、布局取舍、按需选型和验收。
- `references/frontend-brief.md`：用户提供的完整前端工程提示词与使用说明。
- `references/visual-baseline.md`：设计方向、层次、空间、主题及可选纯白/深色基线。
- `references/patterns-and-components.md`：主动发现、比较、取舍与按职责组合组件。
- `references/heroui.md`、`react-bits.md`：版本、集成与许可注意事项。
- `references/liquid-glass-react.md`：液态玻璃固定源码、参数、浏览器兼容与无障碍组合方式。
- `references/lessons-and-acceptance.md`：任务整体成本、具体场景、真实视觉审查、停止条件及 A–F 情境判定。
- `references/source-policy.md`、`upstreams.json`：源码核验流程与锁定提交。

首次获取可使用 `git clone https://github.com/TimYuhong/minimal-product-ui.git`。
维护时先检查 Git 状态并保留已有修改；需要同步远端时再 `git pull --ff-only`。
编辑技能及所需参考并校验；提交、推送和发布仅在用户明确要求时执行。
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

先按任务和现有项目筛选候选；准备采用或实质定制组件时，读取匹配版本的真实源码、
类型、样式与许可，记录来源。Git 和 Python 3.10+ 可用后，按需选择来源，例如在仓库根目录运行：

```sh
python skills/minimal-product-ui/scripts/ui_sources.py fetch --source shadcn-ui
python skills/minimal-product-ui/scripts/ui_sources.py verify --source shadcn-ui
```

上面的命令只处理 shadcn/ui；可重复 `--source` 选择多个需要的库。
`upstreams.json` 提供 **16 个可选来源**：shadcn/ui、Radix Primitives、HeroUI、React Bits、
Magic UI、Aceternity UI、Lucide、Morphicons、Motion、Tailwind CSS、react-resizable-panels、
dnd-kit、Zustand、TanStack Query、Recharts、Liquid Glass React。
其中 15 个使用固定 commit 的 Git sparse checkout；Aceternity 使用官方公开注册表的逐文件 SHA-256 快照，
包含 114 个公开 `registry:ui` 条目的原 JSON 和实际提取源码，不下载 blocks 或付费 templates。
源码位于技能内的 `assets/upstream/<source-id>/`，保留来源与许可证据，不运行上游安装/构建脚本。
按需粒度为来源库；Aceternity 的单组件查看仍先核验该库完整快照，不代表单组件下载。

只有明确进行全库维护时，使用 `fetch --all` 或 `verify --all`。
`--all` 与 `--source` 互斥；裸 `fetch` / `verify` 现在以用法错误退出，零下载、零缓存修改。
这是对旧默认行为的有意收紧，旧脚本需补 `--source <id>` 或明确的 `--all`；已有显式选择命令不变。
`inspect` 与 `refresh-registry` 不支持 `--all`，分别继续要求单来源和 `--source aceternity-ui`。

下载目录由脚本相对技能位置解析，是 Git 忽略的独立上游 checkout，不混入本仓库提交。
公开的锁定清单与脚本使其他使用者可以按相同版本获取源码；校验检查 Git origin、HEAD、本地修改、
关键文件，或注册表原文哈希及全部提取源码。若注册表远端已经变化且缓存缺失，获取会失败，
需要维护者明确更新快照，不能保证上游永久保留旧内容。离线且未取得源码时不能冒称官方实现。

这些快照供源码核验，不意味着应安装开发分支依赖或升级现有项目。
项目采用其他版本时，应先获取与实际安装版本匹配的官方 tag/commit，并记录证据。
详细流程见 [source-policy.md](skills/minimal-product-ui/references/source-policy.md)。

初筛后需要深入核验某个候选时，查看对应实现，例如在技能目录执行：

```sh
python scripts/ui_sources.py inspect --source morphicons --file src/react/index.tsx
python scripts/ui_sources.py inspect --source aceternity-ui --component sidebar
python scripts/ui_sources.py inspect --source liquid-glass-react --file src/index.tsx
```

下载的是参考源码，不是在业务项目安装 16 套依赖；当前项目需要哪个能力才选择哪个来源。

液态玻璃来源为 [rdev/liquid-glass-react](https://github.com/rdev/liquid-glass-react)，
源码、示例和 MIT 许可下载到 `skills/minimal-product-ui/assets/upstream/liquid-glass-react/`。
仅获取这一个来源可使用 `fetch --source liquid-glass-react`，再运行 `verify --source liquid-glass-react`。
本次登记源码版本为 1.1.1；使用前仍需核对目标项目、实际发布版本和专项参考中的限制。

## 校验

Python 3.10+，校验依赖独立于 React 项目；可在仓库内使用虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -B scripts/validate_skill.py
.\.venv\Scripts\python.exe -B scripts/validate_repository.py
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

本地校验检查技能结构、YAML 元数据、内部引用及锚点、公开文件中的个人绝对路径与校验器回归用例；
CLI 选择测试通过 mock 证明缺省/冲突参数不会触发下载、显式选择只操作指定来源，不依赖网络。
维护时还需按 [A–F 情境](skills/minimal-product-ui/references/lessons-and-acceptance.md#scenario-checks)
按改动选择情境并记录规则走读和实际行为各自的结果与证据，不能以结构校验替代设计判断。
新建页面/明显视觉重构按同一文件的视觉闭环运行、查看真实截图、修复并复验；
浏览器不可用时明确标为未完成视觉验证，构建或 mock 不能证明页面视觉/真实业务通过。
审查方法借鉴 taste-skills 的四项诊断思想（固定来源和取舍见验收参考），无新增外部 Skill 依赖。

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
