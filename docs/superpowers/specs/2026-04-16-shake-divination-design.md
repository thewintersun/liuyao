# 摇动起卦功能设计文档

## 概述

为六爻AI排盘应用增加"摇动起卦"方式，用户无需实体硬币即可完成起卦。通过手机摇一摇（加速度传感器）或点击按钮触发虚拟硬币投掷，3D 动画展示 3 枚铜钱翻转结果，逐次完成 6 爻的录入。

## 核心决策

| 项目 | 选择 | 理由 |
|------|------|------|
| 触发方式 | 摇一摇 + 按钮 fallback | 移动端体验优先，桌面端兼容 |
| 页面融合 | 改造 YaoInput 页面，增加模式切换 | 保持流程简洁，不增加新路由 |
| 硬币动画 | 3D 翻转硬币（3 枚同时抛起翻转） | 视觉冲击力强，贴近真实体验 |
| 推进方式 | 逐次推进，每次确认后下一爻 | 仪式感强，用户参与度高 |
| 页面布局 | 上进度条 + 中硬币动画区 | 紧凑清晰，信息一目了然 |
| 随机算法 | 纯随机 50/50 | 与真实硬币一致，简单可靠 |
| 完成过渡 | 结果汇总 + 手动点击"开始排盘" | 给用户回顾确认的机会 |

## 页面结构

### YaoInput 页面改造

```
YaoInput 页面
├── 顶部：时间选择器（沿用现有年月日时下拉框，两种模式共用）
├── 模式切换区：两个 tab（"手动输入" / "摇动起卦"）
├── [手动输入模式] — 现有 6 行爻值按钮，逻辑完全不变
└── [摇动起卦模式]
    ├── 进度区：6 个爻位格（横向排列，初爻→上爻）
    │   ├── 已完成：显示爻线符号（▅▅▅ 或 ▅ ▅），金色背景
    │   ├── 当前：高亮边框 + "?" 标记
    │   └── 未完成：灰色暗淡
    ├── 硬币动画区（页面主体）
    │   ├── 等待状态：3 枚铜钱静置
    │   ├── 摇动中：3 枚铜钱 3D 翻转 + 上抛动画（约 1-1.5 秒）
    │   └── 结果展示：铜钱落定，显示正/背面
    ├── 结果文字：如 "一背 — 少阳 ▅▅▅▅▅"
    ├── 操作区：
    │   ├── 摇卦前："摇动手机起卦" 提示文字 + "点击摇卦" 按钮
    │   ├── 结果确认："确认，下一爻" 按钮
    │   └── 全部完成："开始排盘" 按钮
    └── 结果汇总（6 次全部完成后显示）
        └── 6 个爻值一览表
```

### 模式切换交互

- 默认显示"手动输入"模式（保持现有行为不变）
- 切换为"摇动起卦"时，时间选择器保持不变，下方内容替换为摇卦界面
- 两种模式切换时不会丢失已有数据（但切换会重置对方模式的进度）
- 最终提交时，两种模式产出的 `yaoValues` 格式完全一致

## 技术设计

### 设备动作检测

```javascript
// 检测是否支持摇一摇
const supportsMotion = 'DeviceMotionEvent' in window

// iOS 13+ 需要显式请求权限
async function requestMotionPermission() {
  if (typeof DeviceMotionEvent.requestPermission === 'function') {
    const permission = await DeviceMotionEvent.requestPermission()
    return permission === 'granted'
  }
  return true // 非 iOS 或旧版本默认支持
}

// 摇动检测逻辑
// 监听 devicemotion 事件
// 计算加速度向量的变化量（acceleration.x/y/z）
// 当变化量超过阈值（如 15）时判定为一次摇动
// 加入防抖（如 1 秒内只触发一次）
```

**降级策略：**
- `DeviceMotionEvent` 不存在 → 隐藏摇一摇提示，仅显示点击按钮
- iOS 权限被拒 → 同上，降级为按钮
- 桌面浏览器 → 仅按钮模式

### 3D 硬币动画

**硬币外观：**
- 圆形铜钱风格，金色渐变（`#F9D47C → #d4a843`），暗红色文字
- 正面显示"正"字，背面显示"背"字
- 尺寸约 60-72px 直径，3 枚水平排列

**动画效果：**
- CSS `transform: rotateY()` 实现翻转
- `translateY()` 实现抛起/落下
- 3 枚硬币略有时间差（0.1-0.15s 间隔）
- 动画时长约 1-1.5 秒
- 翻转多圈后落定在随机结果面

**实现方式：**
- 纯 CSS animation + JavaScript 控制 class 切换
- 不依赖任何动画库
- 使用 `perspective` 属性增强 3D 效果

### 随机数生成

```javascript
function throwCoins() {
  // 3 枚硬币各自独立 50/50
  const coins = [
    Math.random() < 0.5 ? '正' : '背',
    Math.random() < 0.5 ? '正' : '背',
    Math.random() < 0.5 ? '正' : '背',
  ]
  // 统计背面数量
  const backs = coins.filter(c => c === '背').length
  // backs 直接对应 yaoValue 编码：0=无背(老阴), 1=一背(少阳), 2=二背(少阴), 3=三背(老阳)
  return { coins, yaoValue: backs }
}
```

**概率分布（与真实硬币一致）：**
- 无背(老阴/0): 1/8 = 12.5%
- 一背(少阳/1): 3/8 = 37.5%
- 二背(少阴/2): 3/8 = 37.5%
- 三背(老阳/3): 1/8 = 12.5%

### 数据对接

摇动模式最终产出的数据格式与手动模式完全一致：

```javascript
// sessionStorage 写入（与现有逻辑相同）
sessionStorage.setItem('liuyao_date', JSON.stringify({
  year, month, day, hour
}))
sessionStorage.setItem('liuyao_yaoValues', JSON.stringify([v0, v1, v2, v3, v4, v5]))

// 跳转排盘页（不变）
router.push('/hexagram')
```

后续排盘、分类、AI 解卦流程完全不受影响，零改动。

## 修改范围

### 需要修改的文件

1. **`frontend/src/views/YaoInput.vue`** — 主要改动文件
   - 新增模式切换 UI（tab 组件）
   - 新增摇动起卦的完整交互逻辑
   - 新增硬币 3D 动画
   - 新增摇一摇传感器检测
   - 保持现有手动输入逻辑不变

2. **`frontend/src/views/Home.vue`** — 微调
   - 更新起卦说明文字，提及"摇动起卦"选项
   - 或不改（YaoInput 页面内自行说明）

### 不需要修改的文件

- `Hexagram.vue` — 接收的数据格式不变
- `router/index.js` — 不新增路由
- `src/core/liuyao.js` — 计算引擎不变
- 后端所有文件 — 纯前端功能
- `src/api/index.js` — 无新 API 调用

## 样式约定

- 遵循现有暗色中国风主题（`theme.css` 中的 CSS 变量）
- 铜钱配色：金色渐变 `--color-primary` 系列
- 字体：楷体（KaiTi）
- 最大宽度 480px 移动优先
