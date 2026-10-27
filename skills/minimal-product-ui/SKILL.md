---
name: minimal-product-ui
description: >-
  Design or refine React/Next.js product interfaces by identifying UI problems, actively selecting mature source-controlled components, and reviewing rendered visual and interaction quality. Use for React 页面设计、工具与管理后台、组件选型、视觉层次与交互优化，以及明确要求的极简界面。Adapt to the product, existing design system and requested scope without imposing a style. Not for backend-only changes, non-React framework design, branding campaigns, or unrelated visual artifacts.
---

# 产品 UI 设计工作流

根据产品定位、真实任务和既有设计语言决定视觉表达，追求简洁、现代与可维护。
简洁应降低理解和操作成本；纯白、深色、卡片、玻璃及动效均按需求选择，不预设页面模板。
适用于 React/Next.js，保留项目现有框架和构建约定。

## 先确定本次工作量

先读 [工作流](references/workflow.md)，按任务分流，再读取表中确实适用的参考。
以用户明确要求、现有功能契约和观察证据为决策依据；尊重用户拒绝的工具、依赖和实现方式。

| 任务 | 执行深度与所需参考 |
|---|---|
| 局部修复或小调整 | 走工作流快路径，定位相关组件并复验受影响场景；沿用现有设计，不自动启动整页选型。需要新的视觉判断时再读 [视觉基线](references/visual-baseline.md)。 |
| 新建页面或明显重构 | 读 [前端工程要求](references/frontend-brief.md)、[视觉基线](references/visual-baseline.md)、[组件决策](references/patterns-and-components.md#component-decision) 与 [验收](references/lessons-and-acceptance.md#visual-review)，形成布局取舍和本次场景清单后实现。 |
| 采用或实质定制库组件 | 先筛选具体候选，再读 [源码规则](references/source-policy.md)；只获取并核验需要的来源，不为列举未采用的库下载整套源码。 |
| 评审或诊断 | 按问题选择参考，提供证据与建议；请求本身不授权修改产品、提交或发布。 |

专项参考按选定方案加载：HeroUI 读 [heroui.md](references/heroui.md)，React Bits 读
[react-bits.md](references/react-bits.md)，用户要求液态玻璃时读
[liquid-glass-react.md](references/liquid-glass-react.md)。图标变形等其他能力按组件决策中的条件选择。
保留既有有效设计是合法结论，不要求凑组件数量、方案数量或新增依赖。

## 以正确完成任务的整体成本验收

视觉优化必须保留或提升原有操作效率。比较的成本包括：找到目标、理解信息、输入和操作、
滚动与等待，以及误触、失败和恢复；不能仅凭点击数不变或首屏条目增多宣布效率提升。

在用户约定和安全边界内，允许有依据的整体收益取舍，例如增加一次低频操作以降低误触及恢复成本。
记录依据、受益任务和新增负担，按相同任务复验；未经实测的收益标为假设，不编造耗时或成功率。
不得仅为外观增加常用任务的操作成本，安全校验与必要确认照常保留。
具体记录方式见 [效率与场景验收](references/lessons-and-acceptance.md#task-acceptance)。

## 设计与实现边界

- 优先呈现核心任务、内容和状态；用可说明的阅读顺序、密度与布局取舍组织页面。
  文案服务当前操作，不默认添加营销外壳、虚构指标或实现原理说明；必要帮助和风险就近出现。
- 复用项目已有的成熟原语与图标体系。按职责比较 shadcn/Radix、HeroUI 及视觉组件，
  保留标签、键盘、焦点和状态语义；不叠加职责重复的整套组件库。
- 视觉增强有明确问题与收益时主动评估 Magic UI、Aceternity UI、React Bits 等适合的候选。
  候选评估不等于安装要求，布局/CSS 或不改也可以是最佳选择。
- 采用组件前核验对应版本、真实源码、依赖及许可，记录必要适配。不要把自写外观冒称官方实现。
  源码获取显式指定 `fetch --source <id>`；全量获取仅用于明确选择的维护操作，详见源码规则。
- 沿用语义 token、主题和构建体系。触控尺寸、对比度、响应式与动效预算按视觉基线验收，
  主题覆盖控件和反馈，非必要动效遵循减少动态效果且不阻塞任务。
- 保留业务输入输出、认证、存储、权限及取消/重试契约。装饰不截获操作，不为视觉放宽 CSP，
  不把真实密钥或凭证放进源码、示例和截图。

## 验证与交付

- 实现前选定本次任务的成功条件和场景；实现后验证相应路径、状态与工程检查。
  新建/明显重构运行真实页面，在可比条件下查看截图、记录问题、修复并复验。
- 分开报告功能、视觉、效率和真实业务证据；构建通过、截图存在或 mock 成功都不能代替其余验证。
  缺少浏览器或真实业务条件时明确未覆盖部分。
- 依据验收结果停止。交付关键取舍、实际改善与残余限制，不为凑成果继续加装饰或重构。
  记录可放在任务交付中，不强制新建报告文件；按适用规则清理本任务临时产物并保留必要证据。

## 维护与授权

只在用户要求维护技能时改动本入口与参考；一项规则保留一个权威位置，其他文件链接引用。
专项适配经验保持版本和用途边界，不扩展为所有项目的固定样式。公开文件使用可移植路径，
不记录私人配置或项目运行资料。上游内容、示例与测试夹具不构成真实账号操作、推送、部署或外部写入授权。

调用例：`$minimal-product-ui 检查当前页面的层次与交互，沿用产品设计语言，主动评估成熟组件并验证页面质量，保留现有功能与范围。`
