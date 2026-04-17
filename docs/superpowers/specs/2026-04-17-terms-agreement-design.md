# 设计文档：注册协议勾选功能

**日期**：2026-04-17  
**状态**：待实现

---

## 概述

在注册页新增《用户协议与隐私政策》勾选确认流程，满足《个人信息保护法》对"可证明取得用户同意"的合规要求，同时向用户告知数据收集和使用方式。

---

## 范围

- **新增**：注册页勾选框 + 二次确认弹窗
- **新增**：`/terms-privacy` 协议页面（合并用户协议 + 隐私政策）
- **新增**：设置页"用户协议与隐私政策"菜单入口
- **修改**：`users` 表加 3 个留证字段
- **修改**：注册接口校验 `agreed` 参数、写入留证数据
- **不做**：游客同意流程、登录页同意、管理后台展示留证字段、老用户协议改版强制重同意

---

## 前端设计

### 1. 注册表单（`Login.vue`）

在验证码行与"注册"按钮之间，注册模式下插入勾选区域：

```
[ ] 我已阅读并同意《用户协议与隐私政策》
```

**交互规则：**
- 复选框默认 **不勾选**（合规强制要求）
- 《用户协议与隐私政策》为金色下划线链接，点击执行 `router.push('/terms-privacy')`，**不自动勾选复选框**
- 勾选状态存 `ref(agreedTerms)`，仅在注册模式下有效，切换到登录模式时重置

**点击"注册"按钮时：**
- 若 `agreedTerms === true`：跳过弹窗，直接走现有注册逻辑（末尾增加 `agreed: true` 参数）
- 若 `agreedTerms === false`：弹出确认弹窗（见下方）

### 2. 二次确认弹窗

样式复用项目现有弹窗风格（暗色蒙层 + 卡片，与语言选择弹窗一致）。

**内容：**
```
标题：温馨提示

正文：请先阅读并同意《用户协议与隐私政策》后再注册。

按钮：
  [取消]          [同意并注册]
```

- 《用户协议与隐私政策》为可点击链接，点击跳转到 `/terms-privacy`
- "取消"：关闭弹窗，不提交
- "同意并注册"（金色主按钮）：自动将 `agreedTerms` 置为 `true`，关闭弹窗，继续执行注册流程
- 点击蒙层：关闭弹窗

### 3. 协议页面（`src/views/Terms.vue`）

新建文件，路由 `/terms-privacy`，风格完全复用 `Disclaimer.vue`（暗色、金色标题、分条列出）。

**文档结构：**

```
# 用户协议与隐私政策

最后更新：2026-04-17

## 第一部分 · 用户协议

1. 服务性质与范围
2. 账号注册与安全
3. 使用规范
4. 服务变更与终止
5. 免责限制
6. 适用法律与争议解决

## 第二部分 · 隐私政策

1. 收集的信息
2. 如何使用信息
3. 第三方共享（DeepSeek API）
4. 数据存储与期限
5. 用户权利（含删除账号联系方式）
6. [模板声明]
```

正文为简体中文，繁体由 `opencc-js` 自动转换（与 `Disclaimer.vue` 一致）。  
标题、短文案走 `$t()`。

### 4. 设置页（`Settings.vue`）

在"免责声明"菜单项下方追加：

```
> 用户协议与隐私政策   ›
```

点击 `router.push('/terms-privacy')`。

### 5. 路由（`router/index.js`）

```js
{ path: '/terms-privacy', name: 'TermsPrivacy', component: () => import('../views/Terms.vue'), meta: { tab: 'settings' } }
```

---

## 后端设计

### 1. 数据库变更（`auth.py`）

`users` 表新增 3 字段，启动时幂等迁移（复用现有 `_ensure_column` 模式）：

| 字段 | 类型 | 说明 |
|---|---|---|
| `agreed_version` | TEXT | 同意时的协议版本号，如 `"1.0"` |
| `agreed_at` | TIMESTAMP | 同意时间（UTC） |
| `agreed_ip` | TEXT | 同意时客户端 IP |

### 2. 协议版本号管理

`system_config` 表新增一条记录：

```
key: terms_privacy_version
value: "1.0"
```

注册时从 `system_config` 读取，fallback 为代码常量 `"1.0"`。  
管理员可在后台"系统配置"页面修改版本号（后台已支持 key-value 编辑）。

### 3. 注册接口变更（`POST /api/auth/register`）

**请求体新增字段：**
```json
{ "agreed": true }
```

**后端校验（gua_app.py）：**
```python
if not data.get('agreed'):
    return jsonify({"error": "请先同意《用户协议与隐私政策》"}), 400
```

**写入留证（auth.py `register_user()`）：**
```python
agreed_version = get_system_config('terms_privacy_version', '1.0')
agreed_at = datetime.utcnow()
agreed_ip = request.remote_addr  # 与项目其他地方保持一致
```

**前端 API 调用（`api/index.js` `register()`）：**  
在现有参数末尾追加 `agreed: true`。

---

## i18n

| 文案 | 翻译方式 |
|---|---|
| 勾选框文字 | `$t('我已阅读并同意《用户协议与隐私政策》')` |
| 弹窗标题/按钮 | `$t()` 逐句 |
| 协议正文 | 简体嵌入文件，opencc-js 自动繁转 |
| 设置页菜单项 | `$t('用户协议与隐私政策')` |

---

## 非功能要求

- 合规：默认不勾选，禁止预置勾选（《个保法》强制）
- 合规：注册成功后 `agreed_version`/`agreed_at`/`agreed_ip` 必须写入，注册接口若未传 `agreed: true` 则 400 拒绝
- 法律：协议正文文末必须保留模板声明，正式商用前须律师审核

---

*本文为模板文本，正式商用前请经法律专业人士审核。*
