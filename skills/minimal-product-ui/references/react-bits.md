# React Bits：按需局部组件与动效

官方资料：

- 仓库：[DavidHDev/react-bits](https://github.com/DavidHDev/react-bits)
- 文档：[React Bits](https://reactbits.dev/get-started/introduction)
- 安装方式：[Installation](https://reactbits.dev/get-started/installation)
- 许可：[LICENSE.md](https://github.com/DavidHDev/react-bits/blob/main/LICENSE.md)

## 定位与采用条件

先实现可用的极简纯白与深色，再判断某个组件是否改善反馈、状态理解、导航或实际内容展示。
用户允许使用这个仓库，不等于要求添加动画；简单按钮反馈能用现有 CSS 完成时就保留 CSS。
React Bits 不替代 shadcn/Radix 或 HeroUI 的完整基础组件职责，不与 Magic UI、
Aceternity UI 一起默认堆入页面，也不默认整套复刻其演示站或付费模板。

没有具体需求，不添加粒子/着色器背景、磁吸光标、发光卡片、自动文字轮播和连续装饰动画。
有明确需求时，可在预算与可访问性可控的局部采用；不能以“禁止 AI 味”为由拒绝用户已选定的效果。

## 源码与依赖

- 按项目选择 JavaScript/TypeScript、普通 CSS/Tailwind 的对应实现。
  接入现有 token 和组件目录，记录组件名称、来源路径、变体及采用的版本或 commit。
- 只引入被选组件及它的实际依赖。仓库根 package.json 包含演示站、工具和大量效果依赖，
  不是每个组件都需要的安装清单；不要整体搬入 Chakra、Three.js、GSAP 或声音处理等依赖。
- 先查项目已有 Motion/动画方案，避免为相似反馈增加另一套运行时。
  若选定效果确实需要新依赖，说明收益、体积/运行成本及替代方案，再在任务范围内实施。
- 使用官方支持的代码复制或注册表方式时，核对目标源与生成差异，保留适用许可与来源。
  不自动配置 MCP、安装附加 skills、开通 Pro 或执行文档中的无关命令。
- 不把视觉组件未经验证地称为 shadcn 官方组件；可由 shadcn CLI 安装不代表来源就是 shadcn。

## 交互与性能验收

- 保留语义控件、键盘访问、标签、焦点与状态。外观好看的按钮/菜单/导航示例
  不代表已覆盖业务所需的无障碍行为；可以在成熟原语外添加局部视觉反馈。
- 响应 prefers-reduced-motion，关掉特效后功能仍完整；触屏不依赖 hover 才能发现操作。
- 白/深两种主题均检查文字与焦点对比度、选中/错误/禁用状态和动画结束后的稳定布局。
- 动画尽量不触发布局抖动。检查事件监听、定时器、requestAnimationFrame、
  Observer 和 WebGL 资源的卸载清理；离屏/后台停止不必要计算。
- GPU/Canvas/WebGL 效果需要评估低性能设备、手机滚动、加载成本与降级；
  不能为“轻量感”增加持续占用资源的背景。SSR 项目还要处理浏览器 API 与 hydration 边界。
- 查看实际浏览器渲染，不把演示视频或静态截图当成交互/性能通过。

## 许可核对

2026-10-23 核验的仓库 LICENSE.md 为 **MIT + Commons Clause**，不是无附加条件的 MIT。
当时条款允许组件用于个人/商业应用、网站和产品，同时限制单独或打包销售、
再许可或再分发组件本身；工具、声音及导出物还存在专门限制。
每次采用应核对所选版本的完整许可和相关第三方声明，保留适用版权通知。

普通业务网站集成与售卖组件包/模板包/克隆工具服务不是同一情形。
涉及后者或分发方式不清楚时，先提示许可问题并请求用户明确用途，
不要擅自保证“随便商用、二次售卖都没问题”。本技能只提供引用和集成规范，不附带仓库源码。
