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
- `references/visual-baseline.md`：双主题、排版、空间和反馈基线。
- `references/patterns-and-components.md`：React 生态按需选型。
- `references/heroui.md`、`react-bits.md`：版本、集成与许可注意事项。
- `references/lessons-and-acceptance.md`：设计教训及验收情境。

首次获取可使用 `git clone https://github.com/TimYuhong/minimal-product-ui.git`。
维护时先 `git pull --ff-only`，编辑技能及所需参考，校验后提交并 `git push`。
不要强推覆盖远端变更，也不要把账号凭证、项目私有配置或业务输出放入仓库。

## 本机接入

本机维护目录为 `E:\tools\skill-repos\personal-ui-skills`。
`%USERPROFILE%\.codex\skills\minimal-product-ui` 是指向本仓库技能目录的 Junction，
不是第二份副本；修改或拉取后使用同一份源文件，无需重新复制安装。

其他 Windows 机器可在克隆后，从仓库根目录运行：

```powershell
$repoRoot = (Resolve-Path .).Path
$skillsDir = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME 'skills' } else { Join-Path $env:USERPROFILE '.codex\skills' }
$skillLink = Join-Path $skillsDir 'minimal-product-ui'
if (Test-Path -LiteralPath $skillLink) { throw '目标已存在，请先检查其来源；不要直接覆盖。' }
New-Item -ItemType Directory -Path $skillsDir -Force | Out-Null
New-Item -ItemType Junction -Path $skillLink -Target (Join-Path $repoRoot 'skills\minimal-product-ui')
```

不要移动仍被 Junction 使用的源目录。迁移路径前先核对链接目标，保留源文件。

## 校验

Python 3.10+，校验依赖独立于 React 项目；可在仓库内使用虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -B scripts/validate_skill.py
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

本地校验检查技能结构、YAML 元数据、内部引用及校验器回归用例。
结构校验不证明实际 UI 设计、浏览器行为或真实业务成功；行为验收见技能内的情境清单。

自动校验模板位于 `maintenance/validate-workflow.yml`，当前尚未启用 GitHub Actions。
需要具备工作流写入权限时，再将模板放到 `.github/workflows/validate.yml` 并提交。
维护技能本身不需要额外授予 OAuth `workflow` 权限。

## 第三方 UI 来源

React 组件可以按项目需要选择 shadcn/Radix、HeroUI，局部视觉组件可以选择 React Bits、
Magic UI、Aceternity UI；其他生态工具按技能中的适用条件使用。
本仓库只保存原创规范与上游引用，**不包含这些库的源码或演示站**，不需要先下载整库或安装 UI 依赖。

需要修改某个组件的上游源码时，再按实际组件、版本、许可与维护目标决定是否 fork 或下载。
采用的源码应记录来源/版本/改动并保留适用声明，不能把别人的代码换上本仓库的许可。
尤其注意 React Bits 的 MIT + Commons Clause 附加限制，以及 HeroUI 不同版本和文件的许可核对。
查阅文档不需要额外注册 MCP 或安装第三方 skills。
