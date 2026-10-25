# Liquid Glass React：局部液态玻璃

用户明确需要液态玻璃时读取。保留项目既定主题，将材质应用于指定表面，
例如弹窗、工具栏或浮层；加入来源不构成自动美化所有卡片或替换业务组件的要求。

## 来源与实际文件

- 官方仓库：[rdev/liquid-glass-react](https://github.com/rdev/liquid-glass-react)。
- 来源 ID：`liquid-glass-react`，完整 commit 由 [upstreams.json](upstreams.json) 锁定。
  本次核验 `ac48eab18d1f7f444ae30002d240cae29c863a21`，源码 package.json 版本 `1.1.1`。
- 本地源码：`../assets/upstream/liquid-glass-react/`，上游 MIT 许可位于 checkout 根目录 `LICENSE`。
  复制/修改源码时保留原版权与许可；`src/shader-utils.ts` 还注明改编自 `shuding/liquid-glass`，保留来源注释。
- 必读：`src/index.tsx`（默认导出、滤镜及事件）、`src/shader-utils.ts`（位移图生成）、
  `src/utils.ts`（内嵌位移图）、`package.json`、`LICENSE`。
  `liquid-glass-example/src/pages/index.tsx` 是参数和布局示例，不能直接当作生产业务页面。

从技能目录按需获取、核验和查看：

```sh
python scripts/ui_sources.py fetch --source liquid-glass-react
python scripts/ui_sources.py verify --source liquid-glass-react
python scripts/ui_sources.py inspect --source liquid-glass-react --file src/index.tsx
```

快照用于核验，不会安装项目依赖或执行上游构建。采用 npm 包时先核对实际发布内容与项目版本，
采用源码时按实际改动记录适配；两种方式均遵循 [source-policy.md](source-policy.md)。

## 实现与参数

默认导出为 `LiquidGlass`。当前 peer 依赖为 `react >=18`、`react-dom >=18`，
没有额外的生产运行时依赖；开发依赖和示例 Next.js 依赖不属于组件的安装清单。

实现使用 SVG 位移/色彩分离滤镜、CSS backdrop blur、边缘高光及鼠标位置反馈。
`shader` 模式通过 Canvas 2D 逐像素生成位移图，不是 WebGL；尺寸变化时会重新生成。

| 参数 | 当前公开默认值 | 使用时核对 |
|---|---|---|
| `mode` | `standard` | 可选 `standard`、`polar`、`prominent`、`shader`；按实际浏览器检查 |
| `displacementScale` | `70` | 折射量；在真实背景上观察边缘，不让内容难读 |
| `blurAmount` | `0.0625` | 是计算参数而非直接的 px；上游用它参与 blur 值计算 |
| `saturation` | `140` | 背景饱和度百分比，不作为业务状态色 |
| `aberrationIntensity` | `2` | 色散强度；按需求调节，避免明显彩边干扰文字 |
| `elasticity` | `0.15` | 鼠标弹性；减少动态效果时置零并处理过渡/监听 |
| `cornerRadius` | `999` | 胶囊默认值；随目标表面形状调整 |
| `padding` | `24px 32px` | 公开实现默认值；结合内部原有组件间距，避免双重内边距 |
| `overLight` | `false` | 浅色背景会改变阴影和叠加层，需实际验收，不能仅按主题名称判断 |

`mouseContainer` 可指定跟踪容器；`globalMousePos` 与 `mouseOffset` 同时提供时会跳过内部鼠标监听。
不凭参数名称保证某个设置已经实现“原生系统同款”效果。

## 接入前必须处理的边界

- **SSR**：当前实现会在渲染中访问 `navigator`，effect 中使用 `window`/Canvas。
  Next.js 的 `use client` 本身不保证跳过服务端预渲染；需要真正的客户端加载边界，
  或在保留来源的局部适配中防护浏览器 API，再验证 hydration。
- **语义与 ref**：公开 `LiquidGlass` 的 `onClick` 落在 `div`，未提供按钮的键盘、disabled 或 ARIA 行为；
  公开组件也未透传任意 DOM props/ref。不要直接作为 Radix `asChild` 的替代节点。
  将材质与既有 Button/Dialog 原语分层组合；装饰层不截获指针，焦点环、Escape、焦点返回及名称均保留。
- **样式**：实现含 Tailwind 工具类而没有独立 CSS 文件。项目需要确保采用的类实际生成；
  已使用其他样式方案时，可核验后转换为局部样式，不为材质强制迁移全局样式系统。
  注意默认白字、20px 内容字号和阴影，接入项目 token 并记录这些定制。
- **定位**：默认计算包含 `translate(-50%, -50%)`，并覆盖传入 style 中的 transform。
  检查定位容器及多层高光的坐标；不能直接嵌入普通文档流，或覆盖 Dialog 原有居中/缩放而不验收。
- **尺寸**：上游挂载及 window resize 时测量，缺少 ResizeObserver。
  内容、字体、展开状态或父容器尺寸变化时需要对应适配，避免位移图和边框停留在旧尺寸。
- **浏览器与 CSP**：上游 README 明示 Safari/Firefox 部分支持，位移可能不可见。
  在目标浏览器检查实际效果；缺少滤镜时保留可读的静态表面和操作，不承诺跨浏览器外观一致。
  检查 SVG `url(#...)`、内嵌/Canvas data URL 与现有 CSP 的兼容性，不为效果放开整个安全策略。

## 视觉、性能与验收

- 在真实浅/深背景、滚动内容和图片上检查折射、色散、边框、文字及焦点；
  纯色背景不能证明折射效果，多叠加 blur 也不能代替来源实现。
- 从 `standard` 和局部尺寸开始评估；`shader` 逐像素生成的成本随面积增长，
  不默认用于大面积或大量列表项，不为展示增加连续全屏计算。
- 上游没有完整的减少动态效果策略；项目需处理 `prefers-reduced-motion`、触屏和后台状态。
  `elasticity=0` 只限制弹性，并不自动取消所有监听、滤镜或 CSS transition。
- 实际检查桌面与手机、支持的主题、键盘/焦点和尺寸变化；检查多个实例的滤镜引用。
  区分源码核验与目标项目浏览器验证，没有接入项目时不声称完成视觉/性能验收。

调用例：

```text
$minimal-product-ui 在现有 React 弹窗局部采用 rdev/liquid-glass-react 的液态玻璃效果。
先核验锁定源码，保留现有 Radix 对话框、表单和焦点行为，检查浏览器降级与减少动态效果。
```
