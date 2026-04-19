# 六爻解卦 Web 应用

基于 iOS 原生应用移植的六爻排盘 + AI 解卦 Web 版本。前端使用 Vue 3，后端使用 Flask，AI 解卦基于 DeepSeek 大语言模型。

---

## 目录

- [项目结构](#项目结构)
- [技术栈](#技术栈)
- [快速启动](#快速启动)
- [前端架构](#前端架构)
- [后端架构](#后端架构)
- [核心计算引擎](#核心计算引擎)
- [API 接口文档](#api-接口文档)
- [页面路由与功能](#页面路由与功能)
- [数据流转流程](#数据流转流程)
- [部署说明](#部署说明)
- [配置说明](#配置说明)

---

## 项目结构

```
web/
├── app.py                  # Flask 主应用 (端口 9001)
├── dialog_manager.py       # AI 多轮对话管理器
├── liuyao_utils.py         # 卦象数据整理工具
├── utils.py                # 邮件发送工具
├── requirements.txt        # Python 依赖
├── .env                    # 环境变量 (API Key、邮箱配置)
├── llm/                    # LLM 模块
│   ├── common/
│   │   ├── base.py         # LLM 基类
│   │   ├── config.py       # Prompt 模板配置
│   │   └── factory.py      # LLM 工厂类
│   └── deepseek/
│       └── client.py       # DeepSeek API 客户端
├── static/                 # 前端构建产物 (npm run build 生成)
│   ├── index.html
│   └── assets/             # JS/CSS 资源
└── frontend/               # 前端源码
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── main.js          # 入口文件
        ├── App.vue          # 根组件
        ├── router/index.js  # 路由配置 (11 条路由)
        ├── api/index.js     # Axios 请求封装
        ├── store/records.js # localStorage 卦例存储
        ├── assets/styles/
        │   └── theme.css    # 全局主题样式
        ├── components/
        │   ├── TabBar.vue   # 底部导航栏 (起卦/记录/设置)
        │   └── NavBar.vue   # 顶部导航栏 (返回+标题)
        ├── core/            # 核心计算引擎
        │   ├── calendar.js      # 天干地支/八字/节气计算
        │   ├── hexagramData.js  # 64 卦八宫数据库
        │   └── liuyao.js        # 排盘引擎 (六亲/六神/世应/伏神)
        └── views/           # 页面组件 (11 个)
            ├── Home.vue         # 起卦须知首页
            ├── YaoInput.vue     # 爻位输入页
            ├── Hexagram.vue     # 排盘展示页
            ├── Category.vue     # 事宜分类选择
            ├── Analysis.vue     # AI 解卦提交
            ├── Chat.vue         # AI 对话页
            ├── Records.vue      # 卦例记录
            ├── Settings.vue     # 设置页
            ├── Guide.vue        # 起卦必读
            ├── Disclaimer.vue   # 免责声明
            └── Feedback.vue     # 建议反馈
```

---

## 技术栈

### 前端
| 技术 | 版本 | 用途 |
|------|------|------|
| Vue 3 | ^3.4.0 | 响应式 UI 框架 |
| Vue Router | ^4.3.0 | SPA 路由管理 |
| Vite | ^5.4.0 | 构建工具 + 开发服务器 |
| Axios | ^1.7.0 | HTTP 请求 |
| marked | ^12.0.0 | Markdown 渲染 (AI 回复) |

### 后端
| 技术 | 版本 | 用途 |
|------|------|------|
| Flask | 2.3.3 | Web 框架 |
| OpenAI SDK | 0.28.0 | DeepSeek API 调用 |
| python-dotenv | - | 环境变量管理 |
| requests | - | HTTP 请求 |

### 设计风格
- 深色中国风主题：深黑背景 `#141414` + 金色点缀 `#F9D47C`
- 楷体字体：`STKaiti / KaiTi / 楷体`
- 最大宽度 480px 居中布局，适配桌面和移动端
- 无框架 CSS，纯手写响应式样式

---

## 快速启动

### 环境要求
- Python 3.8+
- Node.js 16+
- npm

### 1. 安装依赖

```bash
# 后端依赖
cd web
pip install -r requirements.txt

# 前端依赖
cd frontend
npm install
```

### 2. 构建前端

```bash
cd web/frontend
npm run build
# 构建产物输出到 web/static/
```

### 3. 启动服务

```bash
cd web
python app.py
# 服务运行在 http://localhost:9001
```

### 开发模式

开发时可以使用 Vite 的热重载功能：

```bash
# 终端 1: 启动后端
cd web
python app.py

# 终端 2: 启动前端开发服务器
cd web/frontend
npm run dev
# 前端 http://localhost:3000，API 请求自动代理到 9001
```

---

## 前端架构

### 路由设计

应用共 11 条路由，分属 3 个 Tab 组：

| 路由 | 组件 | Tab 分组 | 说明 |
|------|------|----------|------|
| `/` | Home.vue | 起卦 | 起卦须知首页 |
| `/yao-input` | YaoInput.vue | 起卦 | 爻位输入 (时间+6爻) |
| `/hexagram` | Hexagram.vue | 起卦 | 排盘结果展示 |
| `/category` | Category.vue | 起卦 | 所问事宜分类选择 |
| `/analysis` | Analysis.vue | 起卦 | AI 解卦提交 |
| `/chat` | Chat.vue | 起卦 | AI 多轮对话 |
| `/records` | Records.vue | 记录 | 已保存卦例列表 |
| `/settings` | Settings.vue | 设置 | 设置菜单 |
| `/guide` | Guide.vue | 设置 | 起卦必读指南 |
| `/disclaimer` | Disclaimer.vue | 设置 | 免责声明 |
| `/feedback` | Feedback.vue | 设置 | 建议反馈 |

### 导航组件

- **TabBar**：底部标签栏，仅在根页面（`/`、`/records`、`/settings`）显示，包含"起卦"、"记录"、"设置"三个标签
- **NavBar**：顶部导航栏，在非根页面显示，包含返回按钮和页面标题

### 数据存储

- **sessionStorage**：页面间临时数据传递
  - `liuyao_date` - 起卦时间
  - `liuyao_yaoValues` - 6 个爻的值
  - `liuyao_guaXiangInfo` - 排盘结果（传给后端 AI）
  - `liuyao_category` - 所问事宜分类
  - `liuyao_sessionId` - AI 对话会话 ID
  - `liuyao_initialMessage` - AI 首次解卦回复
- **localStorage**：持久化数据
  - `liuyao_records` - 已保存的卦例记录列表

### 主题色变量 (CSS Custom Properties)

```css
--color-primary: #F9D47C      /* 金色主色 */
--color-primary-alt: #EBBD59  /* 金色按下态 */
--color-bg: #141414           /* 深黑背景 */
--color-card: #202020         /* 卡片背景 */
--color-text: #D9D9D9         /* 主文字色 */
--color-text-secondary: #888  /* 辅助文字色 */
--color-border: rgba(249,212,124,0.5)  /* 金色半透明边框 */
--color-user-bubble: #59B300  /* 用户聊天气泡色 */
--color-danger: #FF4444       /* 删除/警告色 */
```

---

## 后端架构

### Flask 应用 (`app.py`)

Flask 以单一服务同时承载 API 接口和前端静态文件：

- **端口**: 9001
- **静态文件**: 手动路由 `web/static/` 目录
- **SPA Fallback**: 任意未匹配路径返回 `index.html`，由前端 Vue Router 处理路由
- **无签名验证**: 与 iOS 版本不同，Web 版同源部署，移除了 HMAC-SHA256 签名验证

### 对话管理器 (`dialog_manager.py`)

- 使用 `OrderedDict` 管理多用户会话
- 最大同时 100 个会话
- 会话超时时间 24 小时
- 自动清理过期会话
- 对话历史超过 token 限制时自动裁剪

### LLM 模块 (`llm/`)

- 工厂模式，支持扩展多个 LLM 提供商
- 当前实现：DeepSeek（通过 OpenAI 兼容 API）
- 模型：`deepseek-chat`
- 支持流式/非流式响应

---

## 核心计算引擎

前端 `src/core/` 目录包含三个核心模块，完整移植自 iOS 原生代码：

### calendar.js — 天干地支计算

| 函数 | 功能 |
|------|------|
| `getJieqi(year, month)` | 计算指定年月的节气日期 |
| `getYearGanZhi(year, month, day)` | 年干支（立春换年） |
| `getMonthGanZhi(year, month, day)` | 月干支（节气换月） |
| `getDayGanZhi(year, month, day)` | 日干支（基于 JDN 推算） |
| `getHourGanZhi(dayStem, hour)` | 时干支（日干定时支） |
| `getFullBaZi(y, m, d, h)` | 完整八字（年月日时四柱） |

关键算法：
- 日柱推算参考点：1901-01-01 = 乙卯日 (序号 16)
- 年柱以立春为界换年，月柱以节气为界换月
- 节气日期使用天文近似公式计算

### hexagramData.js — 64 卦数据库

- 八宫 × 八卦 = 64 卦完整数据
- 每卦包含：卦名、六爻地支、六亲、世应位置
- 包含伏神字典 (`fushen_dict`)
- 包含卦宫五行字典 (`gua_gong_wuxing_dict`)
- 包含变卦六亲替换字典 (`biangua_liuqin_replace_dict`)

### liuyao.js — 排盘引擎

核心类 `Liuyao`，提供以下功能：

| 方法 | 功能 |
|------|------|
| `setDate(y, m, d, h)` | 设置起卦时间，自动计算八字 |
| `paipan(yaoValues)` | 根据 6 个爻值执行排盘 |
| `getGuaGong()` | 获取主卦 [宫名, 卦名] |
| `getBianGuaGong()` | 获取变卦 [宫名, 卦名] |
| `getMainGuaLiuqin()` | 主卦六亲（6 个） |
| `getBianGuaLiuqin()` | 变卦六亲（6 个） |
| `getLiuShenList()` | 六神列表（6 个） |
| `getFuShen()` | 伏神列表（6 个） |
| `getShiYaoWeizhi()` | 世爻位置 (0-5) |
| `getYingYaoWeizhi()` | 应爻位置 (0-5) |
| `getKongWangDisplay()` | 旬空显示 |
| `getLiuHeLiuChong()` | 六合/六冲 |
| `getYouHunGuiHun()` | 游魂/归魂 |
| `getGuaXiangInfo()` | 完整卦象信息对象（传给后端 AI） |

爻值编码规则（铜钱摇卦）：

| 铜钱结果 | 值 | 对应 |
|----------|-----|------|
| 一背（1个背面） | 1 | 阳爻（少阳） |
| 二背（2个背面） | 2 | 阴爻（少阴） |
| 三背（3个背面） | 3 | 老阳（动爻，阳变阴） |
| 无背（0个背面） | 0 | 老阴（动爻，阴变阳） |

内部编码：`"1"` = 阳，`"2"` = 阴

六神起始规则：根据日干确定起始六神，依次为青龙、朱雀、勾陈、腾蛇、白虎、玄武，从初爻到上爻循环排列。

旬空计算：基于日柱数学公式推算（`dizhi_num - tiangan_num - 1`），而非查表法。

---

## API 接口文档

### POST `/api/receive` — 提交卦象，获取 AI 解卦

请求体：
```json
{
  "gua_xiang_info": {
    "maingua_liuqin": ["官戌土", "父申金", ...],
    "biangua_liuqin": ["孙寅木", "兄子水", ...],
    "liushen": ["勾陈", "腾蛇", ...],
    "fushen": ["兄子水", "官戌土", ...],
    "dgua": ["3", "1", "5", "2"],
    "shiyao": 4,
    "yingyao": 1,
    "kongwang": "申酉",
    "maingua_gong": ["坎宫", "雷火丰"],
    "biangua_gong": ["艮宫", "山火贲"],
    "liuchong": "",
    "youhun": "",
    "bian_liuchong": "",
    "bian_youhun": "",
    "time_info": "癸卯年乙丑月戊寅日己未时"
  },
  "background": "用户输入的所问之事描述",
  "category": { "title": "自占自身", "index": 5 }
}
```

响应：
```json
{
  "status": "success",
  "message": "AI 解卦内容 (Markdown 格式)",
  "session_id": "abc123def456"
}
```

### POST `/api/chat` — 追问对话

请求体：
```json
{
  "session_id": "abc123def456",
  "message": "用户的追问内容"
}
```

响应：
```json
{
  "status": "success",
  "message": "AI 回复内容"
}
```

### POST `/api/feedback` — 提交反馈

请求体：
```json
{
  "feedback": "反馈内容",
  "contact": "联系方式 (可选)"
}
```

响应：
```json
{
  "status": "success",
  "message": "反馈已收到"
}
```

### GET `/api/active_users` — 当前活跃用户数

响应：纯文本数字，如 `3`

---

## 数据流转流程

完整的用户使用流程和数据流转：

```
1. Home (起卦须知)
   │  点击 "开始AI起卦"
   ▼
2. YaoInput (爻位输入)
   │  选择时间 + 6个爻值
   │  → sessionStorage: liuyao_date, liuyao_yaoValues
   ▼
3. Hexagram (排盘展示)
   │  ← sessionStorage: 读取时间和爻值
   │  调用 Liuyao 引擎计算排盘
   │  → sessionStorage: liuyao_guaXiangInfo
   │  可选: 保存到 localStorage (卦例记录)
   │  点击 "解卦"
   ▼
4. Category (事宜分类)
   │  选择所问事宜类别 (6选1)
   │  → sessionStorage: liuyao_category
   ▼
5. Analysis (解卦)
   │  输入所求之事描述 (必填)
   │  ← sessionStorage: 读取 guaXiangInfo + category
   │  POST /api/receive → 获取 AI 解卦结果
   │  → sessionStorage: liuyao_sessionId, liuyao_initialMessage
   ▼
6. Chat (AI对话)
      ← sessionStorage: 读取 sessionId + initialMessage
      显示 AI 解卦结果 (Markdown 渲染)
      可继续追问: POST /api/chat
```

---

## 部署说明

### 生产部署

1. 构建前端：
```bash
cd web/frontend
npm run build
```

2. 启动 Flask 服务：
```bash
cd web
python app.py
```

3. 访问 `http://服务器IP:9001`

### 反向代理 (Nginx 示例)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:9001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 120s;
    }
}
```

> 注意：AI 解卦接口响应时间较长（约 30 秒），需要设置较大的代理超时时间。

---

## 配置说明

### 环境变量 (`.env`)

| 变量名 | 说明 |
|--------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 |
| `DEEPSEEK_API_BASE` | DeepSeek API 地址 |
| `EMAIL_ADDRESS` | 反馈邮件发送地址 (163 邮箱) |
| `EMAIL_PASSWORD` | 邮箱授权码 |

### Vite 开发配置 (`vite.config.js`)

- 开发服务器端口：3000
- API 代理：`/api/*` → `http://localhost:9001`
- 构建输出目录：`../static`（即 `web/static/`）

---

## 与 iOS 版本的差异

| 特性 | iOS 版本 | Web 版本 |
|------|----------|----------|
| API 签名验证 | HMAC-SHA256 签名 | 无（同源部署） |
| 订阅/内购 | Apple IAP 订阅 | 无 |
| 数据存储 | CoreData | localStorage |
| 服务端口 | 9000 | 9001 |
| 证书管理 | Let's Encrypt (certbot) | 无 |
| 排盘计算 | 客户端 Swift | 客户端 JavaScript |
| AI 对话 | 与服务端共用 | 独立 Flask 实例 |

> 核心排盘逻辑（天干地支、八字、六亲、六神、伏神、世应等）与 iOS 版本完全一致，确保计算结果相同。
