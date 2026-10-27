# 真实源码约束

“优先官方组件”必须有可验证依据，不是先凭记忆写一套，再冠以库名。

## 使用前必须完成

1. 检查目标项目实际包版本、锁文件和已有组件。源码版本需匹配项目；
   本技能的上游快照用于查证，不授权迁移或升级项目。
2. 对初筛后值得采用/进一步比较的候选，若匹配源码尚未取得，运行 `scripts/ui_sources.py fetch --source <id>`。
   `verify` 成功后，读取要使用的组件实现、类型/导出、样式、必要依赖及许可。
   全部来源的 commit 或注册表哈希位于 [upstreams.json](upstreams.json)。
   当前操作目录不固定时，从正在使用的 SKILL.md 所在目录解析脚本和资源，不硬编码个人路径。
3. 默认快照不是实际项目版本时，从官方 tag、对应源码发布包或原仓库取得准确版本，
   核对其 commit；不要以 HEAD 示例解释旧版本 API。
   调整共享锁定清单需属于用户要求维护本技能的范围，不能在普通项目任务里顺手改全局规范。
4. 实现前能指出“来源仓库、tag/commit、组件文件/注册表条目、实际 API、需要的依赖”。
   需要复制或定制时，记录原文件/版本和具体修改，保留适用许可。
5. 基础组件尽量使用已核实实现；业务组合和主题可以自己设计，但要如实区分。
   官方 Button 不能证明整页布局也是官方默认，第三方注册表组件也不是 shadcn 官方组件。

## 源码获取与验证

从本技能目录运行 `python scripts/ui_sources.py fetch --source <id>`，再运行
`python scripts/ui_sources.py verify --source <id>`；支持重复 `--source` 选择多个需要的库。
Git 来源只执行必要的 Git 操作；注册表来源仅下载、校验和提取公开文本，
不执行 upstream 安装、构建、Hook、MCP 注册或代码生成脚本。

源码保存在本技能相对路径 `assets/upstream/`；每份 checkout 保留自己的 origin、
固定 HEAD 和原许可文件。Aceternity 使用官方注册表快照，保存原 JSON、提取源码与许可页面，
逐文件锁定 SHA-256。不向远端重新打包这些源码，不创建无实际用途的 fork。
`verify` 会拒绝缺失文件、不同来源/提交或本地修改；不自动 reset、覆盖或删除用户改动。
被中断的初次下载应保留并先核对状态；未知目录、错误 origin 或脏 checkout 要先说明，
不能为了重试删除来源不明或存在改动的目录。完整且干净的固定版本可直接重复使用，无需重复联网。

如果网络不可用、来源无法核验或许可不清楚，说明未验证的具体部分。
可以进行与该库无关的原生布局/已有组件工作，但不得“猜一个相似实现”并宣称已复用官方源码。
不要为了过关改写验证输出或用整仓 README 代替具体组件源码证据。

## 默认源文件定位

| 来源 | checkout ID | 已锁定快照的典型入口 |
|---|---|---|
| shadcn/ui | shadcn-ui | `apps/v4/registry/new-york-v4/ui/` |
| Radix Primitives | radix-primitives | `packages/react/<component>/src/` |
| HeroUI | heroui | `packages/react/src/components/`、`packages/styles/` |
| React Bits | react-bits | `src/ts-tailwind/` |
| Magic UI | magic-ui | `apps/www/registry/magicui/` |
| Aceternity UI | aceternity-ui | 锁中指定的 `snapshots/<snapshot>/items/<component>/`，保留原路径 |
| Lucide React / 图标数据 | lucide | `packages/lucide-react/src/`、`packages/lucide/src/`、`icons/` |
| Morphicons | morphicons | `src/react/index.tsx`、`src/core/types.ts`、`src/dom/` |
| Liquid Glass React | liquid-glass-react | `src/index.tsx`、`src/shader-utils.ts`、`src/utils.ts`、`liquid-glass-example/src/` |
| Motion | motion | `packages/motion/src/`、`packages/framer-motion/src/`、`packages/motion-dom/src/` |
| Tailwind CSS | tailwindcss | `packages/tailwindcss/src/`、`packages/@tailwindcss-vite/src/` |
| react-resizable-panels | react-resizable-panels | `lib/index.ts`、`lib/components/` |
| dnd-kit | dnd-kit | `packages/react/src/` 及 `packages/dom/` 等共享实现 |
| Zustand | zustand | `src/`、`docs/` |
| TanStack Query | tanstack-query | `packages/react-query/src/`、`packages/query-core/src/` |
| Recharts | recharts | `src/chart/`、`src/component/`、`src/index.ts` |

只读取与任务相关的组件、类型、样式和许可，不一次加载所有仓库全文。
`fetch` / `verify` 必须显式指定 `--source <id>` 或 `--all`；两者互斥，省略时退出并提示用法，
不会选择来源、下载或更改缓存。`--all` 只用于明确需要全库操作的维护任务；不作为普通 UI 工作的默认步骤。
既有显式 `--source` 命令保持兼容，旧的裸 `fetch` / `verify` 调用需补选择参数。
`inspect` 需明确一个来源与 `--file` / `--component` 二选一；`refresh-registry` 仍要求恰好一次
`--source aceternity-ui`，两者不支持 `--all`。命令不安装项目 npm 依赖或执行上游 Hook。

按需粒度是来源库：Git 保持清单中的 sparse checkout；Aceternity 仍获取/核验所选库的完整锁定快照。
`inspect --component` 只缩小输出范围，不是逐组件下载。不要误报为只获取了一个组件。

```sh
python scripts/ui_sources.py inspect --source morphicons --file src/react/index.tsx
python scripts/ui_sources.py inspect --source aceternity-ui --component sidebar
```

`inspect` 先验证来源和锁，再读取指定实现；Aceternity 按组件名定位锁内的实际路径，
同时输出该注册表条目的依赖。对有版本差异的项目，仍需另取匹配版本，快照不自动覆盖项目锁文件。

Aceternity 的远端注册表可能更新。已有完整缓存可离线验证；补缺时远端文件与锁不同，
`fetch` 应失败并保留原目录，不擅自信任新内容。只有明确维护技能时才能运行
`refresh-registry --source aceternity-ui`，它新建快照、检查源码，再更新锁，不覆盖旧快照。
维护者需要检查变更与逐项许可；官方 licence/terms 页面是适用条件的证据，不是统一 MIT 授权。

## 公开仓库要求

README、示例和工具输出说明使用仓库相对路径、可配置参数或标准用户目录变量。
不写维护者电脑的盘符路径、用户名、服务器地址、账号、密钥或私人项目运行记录。
第三方许可证中的原作者信息按许可原文保留，不当作个人路径清理目标。
提交前运行仓库可移植性检查；保持公开说明与实际下载/校验行为一致。
