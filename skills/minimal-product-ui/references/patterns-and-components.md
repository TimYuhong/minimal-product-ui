# 模式与组件选择

先看现有依赖与真实业务，再选最少的必要组件；下面是选择依据，不是安装清单。

## 按场景组织界面

- **短表单/工具站**：紧凑标题、输入、一个主操作、按需结果；无需通用管理后台外壳。
- **批量导入**：保留用户定义的粘贴/文件契约，解析结果靠近输入；
  处理后用真实行状态、筛选与导出，不默认添加大数字统计卡和常驻教程。
- **管理后台**：导航只承载真实模块；页面工具栏聚合搜索、筛选与操作，
  数据区优先列表/表格、行详情和就近状态。复杂度需要时再分栏或加侧栏。
- **长任务**：显示可观察的阶段、进度与失败原因，区分取消等待与撤销已发生的副作用；
  不用动画或假进度代替真实状态。
- **帮助和风险**：常驻一行必要提示或可展开帮助；后果重要的操作在确认时说明，
  不把工程说明、平台声明和隐私卖点铺满首页。

## React 生态按需选用

| 需求 | 来源 ID 与使用条件 | 不需要时 |
|---|---|---|
| 按钮、表单、Tabs、Dialog、菜单 | `shadcn-ui`：需要源码可控的基础组件；`radix-primitives`：需要无障碍交互原语；`heroui`：已有 HeroUI 或选作完整主方案 | 先复用项目；不叠加两套主组件库，不重造焦点/键盘原语 |
| 样式与语义主题 | `tailwindcss`：项目已用或明确选择 Tailwind，核对当前大版本的主题与插件 API | 不为重置颜色迁移构建工具或 Tailwind 大版本 |
| 常规图标 | `lucide`：按钮、状态、导航需要一致图标时，使用 React 绑定或已核验的图标数据 | 不再装一套近似图标库，不用 emoji 代替结构图标 |
| 图标状态变形 | `morphicons`：复制/成功、展开/关闭、播放/暂停等变化能帮助理解操作时 | 不把每个静态图标都变成动画，不替代按钮和状态逻辑 |
| 简单状态 | React 本地状态与现有上下文 | 不为少量字段安装状态库 |
| 跨模块共享客户端状态 | `zustand`：多个视图确实共享状态且本地状态/现有 Context 不再合适时 | 不为少量字段引入全局 store；不与服务器数据缓存重复管理同一状态 |
| 服务器状态缓存/重取/去重 | `tanstack-query`：需要查询生命周期、失效、缓存或乐观更新时 | 简单请求保留合理的现有实现，敏感数据不默认持久化 |
| 布局、离场和手势动画 | `motion`：CSS 难以表达的布局/手势/编排；先复用项目已有 Motion/Framer Motion | 不为一个淡入安装动画运行时，不同时安装两套等价入口 |
| React 局部视觉组件 | `react-bits`：明确要求的局部交互或动效，先查成本和许可 | 不整体搬入演示站，不默认 WebGL/粒子背景 |
| 液态玻璃材质 | `liquid-glass-react`：用户明确选择折射、边缘高光和弹性效果时，先阅读专项参考 | 不替代 Dialog/按钮语义，不自动叠加其他玻璃实现或改整页主题 |
| 精选视觉增强 | `magic-ui`：已完成可用界面后，需要具体的轻量视觉反馈或展示组件时 | 不因为库提供动画卡片就重做工具页面 |
| 特定视觉构图/组件 | `aceternity-ui`：用户明确选择相关样式或某个公开组件确实适用时 | 不套营销模板，不下载付费 blocks/templates，不假定全部 MIT |
| 用户需要可调分栏 | `react-resizable-panels`：需要拖动分隔条、尺寸约束或布局恢复时 | 静态两列用 CSS Grid 即可 |
| 用户需要拖拽排序/移动 | `dnd-kit`：真实排序/移动需求，保留键盘与非拖拽替代操作 | 不因“交互感”添加拖拽 |
| 真实数据图表 | `recharts`：数据比较或趋势确实需要图形表达时，配合空/错状态和必要文字摘要 | 单个数字不必画图，不虚构数据 |

新增依赖前交代必要性与复用结果。使用 shadcn 官方源时核实注册表、许可、
导入路径及兼容性；可记录来源与改动，但不宣称业务布局也是官方模板。

## 版本与来源陷阱

- 矩阵的 ID 对应 `upstreams.json`，操作前按工作流核验。快照不是项目默认安装版本。
- `react-resizable-panels` 是准确包名。缓存包含 `Group`、`Panel`、`Separator` 等当前实现，
  旧版 `PanelGroup`/`PanelResizeHandle` 的示例不能直接混用。
- dnd-kit 当前快照包含新 `@dnd-kit/react` 系列；使用旧 `@dnd-kit/core`/`sortable` 的项目，
  要另取匹配版本，不能只因同属 dnd-kit 就替换 API。
- Motion 的 `motion/react` 与已有 `framer-motion`、Tailwind v3/v4、TanStack Query 大版本，
  都先核对包与导出。Lucide 的 React 组件与 IconNode 数据也不是同一种输入。
- Lucide 含不同来源的图标许可，应读根 LICENSE 与具体图标声明；不要因 API 返回 NOASSERTION 就猜许可。

## Morphicons：可选图标反馈

- 官方来源为 `guillermolg00/morphicons`，React 入口 `morphicons/react`，许可 MIT。
  阅读 `src/react/index.tsx`、`src/core/types.ts` 与 `src/dom/` 的实际行为后使用。
- 接收 IconNode 或 SVG 路径字符串，不能直接把 `lucide-react` 的 React 组件传入。
  可以使用匹配的 Lucide 数据导出或按许可提取所需路径，避免再装整套近似图标库。
- 用在能表达真实操作状态的少数控件上；按钮仍采用既有成熟组件，保留文本/aria-label、焦点和点击目标。
  禁止因“点了有动画”就让静态列表所有图标持续变形。
- 当前源码默认 `reducedMotion="never"`，项目接入应显式选择 `reducedMotion="user"`。
  上游宣称的体积不代替目标构建实测；尤其核对填充图标额外懒加载与同页大量实例的成本。
- 该库内部已有弹簧动画，不为同一图标额外安装 Motion。它也不承担卡片、布局或表单组件职责。

## Aceternity：官方公开注册表

- 官方来源为 `https://ui.aceternity.com/registry.json` 及其逐项注册表 URL。
  本技能缓存公开 `registry:ui` 条目和提取的源码，原 JSON 与源码由 SHA-256 锁对应。
- 不把个人演示仓库冒称官方源码。公开注册表可下载不等于所有条目均采用 MIT；
  当前保存官方 licence/terms 页面作为许可证据，使用前逐项确认免费/Pro 与第三方声明。
- 缓存供本地核验，不重分发组件源码包。付费 blocks、templates 和未取得授权的代码不属于下载范围。
- 普通任务不刷新哈希以绕过失败。需要更新快照时，维护者显式运行
  `python scripts/ui_sources.py refresh-registry --source aceternity-ui`，检查变化和许可后再发布锁定清单。

## Liquid Glass React：可选液态玻璃

官方来源为 `rdev/liquid-glass-react`，默认导出 `LiquidGlass`，MIT 许可。
实现、实际参数与边界见 [liquid-glass-react.md](liquid-glass-react.md)。
SVG 折射、背景模糊、边缘高光和弹性分别控制；与现有 React Bits 玻璃适配比较后选择一种局部方案。
采用前检查 SSR、样式工具类、居中 transform、真实背景及焦点组合，不直接套用演示站。

## HeroUI 的使用边界

用户提供的官方仓库：[heroui-inc/heroui](https://github.com/heroui-inc/heroui)。
可选为 React/Next.js 项目的主组件方案，特别是已有 HeroUI 或需要一致的表单、
选择器、弹窗、数据展示组件时。选用前阅读 [heroui.md](heroui.md)。
按业务需要组织 React 页面，不为借鉴布局再安装另一套 UI 框架。

HeroUI 与 shadcn/Radix 优先择一承担同一层组件职责。不是要求移除 HeroUI 自身的
传递依赖，也不是禁止复用项目里已有的局部组件；需要混用时先明确边界，
避免重复主题、全局 reset、焦点管理和覆盖样式。

## React Bits 的使用边界

用户提供的仓库：[DavidHDev/react-bits](https://github.com/DavidHDev/react-bits)。
它提供可选的组件与动效源码，不是必须整体安装的基础 UI 框架。
准备采用时阅读 [react-bits.md](react-bits.md)：匹配 JS/TS 与 CSS/Tailwind 版本，
核对该组件自己的依赖、许可、可访问性和性能，不把演示站点依赖全部搬进项目。

先做好静态可用的白/深页面，再为真实体验问题选局部组件。
没有明确需求时，不采用粒子、光效背景、光标追踪、文字轮播或 WebGL 作为默认装饰。

范围限定为 React/Next.js。保留项目现有构建、路由、组件和主题约定；
推荐技术栈不构成重写授权，不引入其他框架的 UI 套件作为默认参考。
