# 注册协议勾选功能 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在注册页新增《用户协议与隐私政策》勾选确认流程，合规记录用户同意证据，并提供可查阅的协议文档页面。

**Architecture:** 后端为 `users` 表新增 3 个留证字段，注册接口强制要求 `agreed: true`；前端在注册表单加勾选框 + 二次确认弹窗，新增协议页面 `Terms.vue`，设置页追加入口。

**Tech Stack:** Vue 3 (Composition API, `<script setup>`) · Flask · SQLite · Axios

---

## 文件清单

| 操作 | 文件 | 说明 |
|---|---|---|
| 修改 | `auth.py` | users 表迁移 3 字段 + `register_user()` 写留证 |
| 修改 | `gua_app.py` | `api_register()` 校验 `agreed`，传 IP 给 `register_user()` |
| 修改 | `frontend/src/api/index.js` | `register()` 增加 `agreed` 参数 |
| 新建 | `frontend/src/views/Terms.vue` | 协议文档页面 |
| 修改 | `frontend/src/router/index.js` | 新增 `/terms-privacy` 路由 |
| 修改 | `frontend/src/views/Settings.vue` | 追加"用户协议与隐私政策"菜单项 |
| 修改 | `frontend/src/views/Login.vue` | 注册模式新增勾选框 + 二次确认弹窗 |

---

## Task 1：数据库迁移 — users 表新增留证字段

**Files:**
- Modify: `auth.py`（`init_db()` 函数，约第 55-73 行迁移块之后）

- [ ] **Step 1：在 `auth.py` 的 `init_db()` 函数末尾（现有迁移块之后）追加以下代码**

  找到最后一段迁移（`token_version` 字段），在其后插入：

  ```python
      # 数据库迁移：添加协议同意留证字段
      for col, col_type in [
          ('agreed_version', 'TEXT'),
          ('agreed_at', 'TIMESTAMP'),
          ('agreed_ip', 'TEXT'),
      ]:
          try:
              db.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
              db.commit()
          except Exception:
              pass  # 列已存在
  ```

- [ ] **Step 2：启动后端验证迁移成功**

  ```bash
  cd D:/code/project/liuyao/web
  python -c "from auth import init_db; init_db(); import sqlite3; db = sqlite3.connect('users.db'); print([c[1] for c in db.execute('PRAGMA table_info(users)').fetchall()])"
  ```

  预期输出包含：`'agreed_version'`、`'agreed_at'`、`'agreed_ip'`

- [ ] **Step 3：提交**

  ```bash
  git add auth.py
  git commit -m "feat: add agreed_version/agreed_at/agreed_ip columns to users"
  ```

---

## Task 2：system_config 初始化协议版本号

**Files:**
- Modify: `auth.py`（`init_db()` 函数，Task 1 代码之后）

- [ ] **Step 1：在 Task 1 代码块之后追加版本号种子**

  ```python
      # 初始化协议版本号（若不存在）
      try:
          db.execute(
              "INSERT OR IGNORE INTO system_config (key, value) VALUES ('terms_privacy_version', '1.0')"
          )
          db.commit()
      except Exception:
          pass  # system_config 表可能尚未建立（首次冷启动时顺序由 admin_service 建表）
  ```

  > 注意：`system_config` 表由 `admin_service.py` 的 `init_admin_db()` 建立。`gua_app.py` 在启动时会依次调用 `init_db()` 和 `init_admin_db()`，所以 `system_config` 在 `init_db()` 执行时可能还未建立。用 `try/except` 即可，重试在下次冷启动自动完成；已运行的实例通过管理后台可手动写入。

- [ ] **Step 2：验证**

  ```bash
  python -c "import sqlite3; db = sqlite3.connect('users.db'); print(db.execute(\"SELECT * FROM system_config WHERE key='terms_privacy_version'\").fetchone())"
  ```

  预期：`('terms_privacy_version', '1.0')` 或 `None`（若 system_config 表尚未建立，也正常）

- [ ] **Step 3：提交**

  ```bash
  git add auth.py
  git commit -m "feat: seed terms_privacy_version=1.0 into system_config on init"
  ```

---

## Task 3：后端 — `register_user()` 写入留证数据

**Files:**
- Modify: `auth.py`（`register_user()` 函数，约第 117 行）

- [ ] **Step 1：修改函数签名，新增 3 个参数**

  将第 117 行：
  ```python
  def register_user(username, password, email=None):
  ```
  改为：
  ```python
  def register_user(username, password, email=None, agreed_version=None, agreed_at=None, agreed_ip=None):
  ```

- [ ] **Step 2：修改 INSERT 语句，写入留证字段**

  找到约第 135-138 行的 INSERT：
  ```python
          db.execute(
              'INSERT INTO users (username, password_hash, free_uses, email) VALUES (?, ?, ?, ?)',
              (username, generate_password_hash(password), free_uses, email.strip())
          )
  ```
  替换为：
  ```python
          db.execute(
              'INSERT INTO users (username, password_hash, free_uses, email, agreed_version, agreed_at, agreed_ip) VALUES (?, ?, ?, ?, ?, ?, ?)',
              (username, generate_password_hash(password), free_uses, email.strip(), agreed_version, agreed_at, agreed_ip)
          )
  ```

- [ ] **Step 3：提交**

  ```bash
  git add auth.py
  git commit -m "feat: register_user writes agreed_version/agreed_at/agreed_ip"
  ```

---

## Task 4：后端 — `api_register()` 校验 agreed 并传入留证数据

**Files:**
- Modify: `gua_app.py`（`api_register()` 函数，约第 97-107 行）

- [ ] **Step 1：修改 `api_register()` 函数**

  > `datetime` 和 `admin_service` 已在 `gua_app.py` 顶部引入（第 9、27 行），无需额外 import。

  找到：
  ```python
  @app.route('/api/auth/register', methods=['POST'])
  def api_register():
      if not request.is_json:
          return jsonify({"error": "请求必须是 JSON 格式"}), 400
      data = request.get_json()
      if not validate_captcha(data.get('captcha_id', ''), data.get('captcha_text', '')):
          return jsonify({"error": "验证码错误或已过期"}), 400
      result, error = register_user(data.get('username', ''), data.get('password', ''), data.get('email', ''))
      if error:
          return jsonify({"error": error}), 400
      return jsonify({"status": "success", **result})
  ```

  替换为：
  ```python
  @app.route('/api/auth/register', methods=['POST'])
  def api_register():
      if not request.is_json:
          return jsonify({"error": "请求必须是 JSON 格式"}), 400
      data = request.get_json()
      if not data.get('agreed'):
          return jsonify({"error": "请先同意《用户协议与隐私政策》"}), 400
      if not validate_captcha(data.get('captcha_id', ''), data.get('captcha_text', '')):
          return jsonify({"error": "验证码错误或已过期"}), 400
      # 读取当前协议版本号
      terms_version = admin_service.get_system_config('terms_privacy_version') or '1.0'
      agreed_ip = get_client_ip(request)
      agreed_at = datetime.utcnow()
      result, error = register_user(
          data.get('username', ''),
          data.get('password', ''),
          data.get('email', ''),
          agreed_version=terms_version,
          agreed_at=agreed_at,
          agreed_ip=agreed_ip,
      )
      if error:
          return jsonify({"error": error}), 400
      return jsonify({"status": "success", **result})
  ```

- [ ] **Step 2：手动测试注册接口**

  先测试缺少 agreed 字段被拒绝：
  ```bash
  curl -s -X POST http://localhost:9001/api/auth/register \
    -H "Content-Type: application/json" \
    -d '{"username":"testuser","password":"123456","email":"t@t.com","captcha_id":"x","captcha_text":"x","agreed":false}' | python -m json.tool
  ```
  预期：`{"error": "请先同意《用户协议与隐私政策》"}`

- [ ] **Step 3：提交**

  ```bash
  git add gua_app.py
  git commit -m "feat: api_register validates agreed and writes consent proof"
  ```

---

## Task 5：前端 API — `register()` 增加 agreed 参数

**Files:**
- Modify: `frontend/src/api/index.js`（`register()` 函数，约第 51-56 行）

- [ ] **Step 1：修改函数签名和请求体**

  将：
  ```js
  export async function register(username, password, email, captchaId, captchaText) {
    const response = await api.post('/api/auth/register', {
      username, password, email, captcha_id: captchaId, captcha_text: captchaText
    })
    return response.data
  }
  ```
  改为：
  ```js
  export async function register(username, password, email, captchaId, captchaText, agreed = false) {
    const response = await api.post('/api/auth/register', {
      username, password, email, captcha_id: captchaId, captcha_text: captchaText, agreed
    })
    return response.data
  }
  ```

- [ ] **Step 2：提交**

  ```bash
  git add frontend/src/api/index.js
  git commit -m "feat: register() API adds agreed param"
  ```

---

## Task 6：前端 — 新建协议页面 Terms.vue + 路由 + 设置菜单

**Files:**
- Create: `frontend/src/views/Terms.vue`
- Modify: `frontend/src/router/index.js`
- Modify: `frontend/src/views/Settings.vue`

- [ ] **Step 1：新建 `frontend/src/views/Terms.vue`**

  ```vue
  <template>
    <div class="page terms-page">
      <h2 class="page-title">{{ $t('用户协议与隐私政策') }}</h2>
      <div class="content">
        <p class="updated-at">{{ $t('最后更新：') }}2026-04-17</p>

        <h3>{{ $t('第一部分 · 用户协议') }}</h3>

        <h4>{{ $t('1. 服务性质与范围') }}</h4>
        <p>本应用（六爻AI排盘）提供基于中国传统六爻理论的占卜排盘服务，结合人工智能生成解卦分析，仅供娱乐、文化学习和个人参考之用，不构成任何专业建议。</p>

        <h4>{{ $t('2. 账号注册与安全') }}</h4>
        <p>您需提供真实有效的邮箱地址完成注册。账号由您本人使用，请妥善保管密码。因密码泄露导致的损失由用户自行承担。</p>

        <h4>{{ $t('3. 使用规范') }}</h4>
        <p>禁止通过自动化工具批量调用接口、爬取数据或实施任何可能影响服务稳定性的行为。禁止将本服务用于违法或违反公序良俗的目的。</p>

        <h4>{{ $t('4. 服务变更与终止') }}</h4>
        <p>本应用有权随时修改、暂停或终止全部或部分服务，无需事先通知。对于免费额度的调整，本应用保留最终解释权。</p>

        <h4>{{ $t('5. 免责限制') }}</h4>
        <p>六爻预测结果不保证准确性，不应作为医疗、法律、投资等重大决策依据。因使用本服务产生的任何损失，本应用不承担责任。</p>

        <h4>{{ $t('6. 适用法律与争议解决') }}</h4>
        <p>本协议适用中华人民共和国法律。如发生争议，双方应友好协商解决；协商不成的，提交本应用运营方所在地有管辖权的法院处理。</p>

        <h3>{{ $t('第二部分 · 隐私政策') }}</h3>

        <h4>{{ $t('1. 收集的信息') }}</h4>
        <p>我们收集以下信息：注册时的用户名和邮箱地址；使用服务时的 IP 地址、设备信息；您输入的起卦参数和与 AI 的对话内容；使用记录（时间、次数）。</p>

        <h4>{{ $t('2. 如何使用信息') }}</h4>
        <p>收集的信息用于：提供 AI 解卦服务；账户管理与身份验证；防范滥用和安全防护；改善服务质量（统计分析）。</p>

        <h4>{{ $t('3. 第三方共享') }}</h4>
        <p>您的对话内容（起卦参数、问题描述）将发送至 DeepSeek（深度求索）的 API 进行 AI 处理，DeepSeek 的隐私政策独立适用。除此之外，我们不向第三方出售或共享您的个人信息。</p>

        <h4>{{ $t('4. 数据存储与期限') }}</h4>
        <p>数据存储于服务器本地 SQLite 数据库。账户注销后，您的个人信息将在 30 天内删除（对话记录立即删除）。</p>

        <h4>{{ $t('5. 用户权利') }}</h4>
        <p>您有权查阅、更正或删除您的个人信息，包括申请注销账号。如需行使上述权利，请发送邮件至：<strong>thewintersun@gmail.com</strong>，我们将在 15 个工作日内处理。</p>

        <p class="template-notice">⚠️ 本文为模板文本，正式商用前请经法律专业人士审核。</p>
      </div>
    </div>
  </template>

  <style scoped>
  .content {
    padding: 0 4px;
  }
  .updated-at {
    color: var(--color-text-secondary);
    font-size: 13px;
    margin-bottom: 16px;
  }
  .content h3 {
    color: var(--color-primary);
    font-size: 18px;
    font-weight: bold;
    margin: 24px 0 8px;
    border-bottom: 1px solid var(--color-border);
    padding-bottom: 8px;
  }
  .content h4 {
    color: var(--color-primary);
    font-size: 15px;
    margin: 16px 0 6px;
  }
  .content p {
    color: var(--color-text);
    font-size: 15px;
    line-height: 1.8;
    margin-bottom: 8px;
  }
  .content strong {
    color: var(--color-primary);
  }
  .template-notice {
    margin-top: 24px;
    padding: 12px;
    background: rgba(249, 212, 124, 0.08);
    border: 1px solid var(--color-border);
    border-radius: 4px;
    color: var(--color-text-secondary);
    font-size: 13px;
  }
  </style>
  ```

- [ ] **Step 2：在 `router/index.js` 新增路由**

  在 `/disclaimer` 路由之后插入：
  ```js
  { path: '/terms-privacy', name: 'TermsPrivacy', component: () => import('../views/Terms.vue'), meta: { tab: 'settings' } },
  ```

- [ ] **Step 3：在 `Settings.vue` 追加菜单项**

  找到"免责声明"菜单项：
  ```html
  <div class="menu-item" @click="$router.push('/disclaimer')">
    <span class="menu-title">{{ $t('免责声明') }}</span>
    <span class="menu-arrow">&#8250;</span>
  </div>
  ```

  在其**后面**插入：
  ```html
  <div class="menu-item" @click="$router.push('/terms-privacy')">
    <span class="menu-title">{{ $t('用户协议与隐私政策') }}</span>
    <span class="menu-arrow">&#8250;</span>
  </div>
  ```

- [ ] **Step 4：启动前端验证页面可访问**

  访问 `http://localhost:3000/terms-privacy`，确认：
  - 页面显示"用户协议与隐私政策"标题
  - 两大部分内容完整展示
  - 设置页有新菜单项可跳转

- [ ] **Step 5：提交**

  ```bash
  git add frontend/src/views/Terms.vue frontend/src/router/index.js frontend/src/views/Settings.vue
  git commit -m "feat: add Terms.vue page with route and settings menu entry"
  ```

---

## Task 7：前端 — Login.vue 注册模式新增勾选框 + 二次确认弹窗

**Files:**
- Modify: `frontend/src/views/Login.vue`

- [ ] **Step 1：在 `<template>` 中的验证码行与注册按钮之间插入勾选框**

  找到：
  ```html
  <button class="btn-primary" @click="handleSubmit" :disabled="loading">
  ```

  在其**前面**插入（注册模式下显示）：
  ```html
  <div class="form-group agree-row" v-if="!isLogin">
    <label class="agree-label">
      <input type="checkbox" v-model="agreedTerms" class="agree-checkbox" />
      <span>{{ $t('我已阅读并同意') }}
        <span class="agree-link" @click.prevent="$router.push('/terms-privacy')">{{ $t('《用户协议与隐私政策》') }}</span>
      </span>
    </label>
  </div>

  <!-- 二次确认弹窗 -->
  <div class="terms-overlay" v-if="showTermsDialog" @click.self="showTermsDialog = false">
    <div class="terms-dialog">
      <p class="terms-dialog-title">{{ $t('温馨提示') }}</p>
      <p class="terms-dialog-body">
        {{ $t('请先阅读并同意') }}
        <span class="agree-link" @click="$router.push('/terms-privacy')">{{ $t('《用户协议与隐私政策》') }}</span>
        {{ $t('后再注册。') }}
      </p>
      <div class="terms-dialog-btns">
        <button class="btn-cancel" @click="showTermsDialog = false">{{ $t('取消') }}</button>
        <button class="btn-primary btn-agree" @click="agreeAndSubmit">{{ $t('同意并注册') }}</button>
      </div>
    </div>
  </div>
  ```

- [ ] **Step 2：在 `<script setup>` 中新增响应式状态**

  在 `const loading = ref(false)` 一行之后新增：
  ```js
  const agreedTerms = ref(false)
  const showTermsDialog = ref(false)
  ```

- [ ] **Step 3：修改 `toggleMode()` 函数，切换到登录模式时重置勾选状态**

  找到：
  ```js
  function toggleMode() {
    isLogin.value = !isLogin.value
    email.value = ''
    confirmPassword.value = ''
    captchaText.value = ''
    if (!isLogin.value) {
      refreshCaptcha()
    }
  }
  ```
  替换为：
  ```js
  function toggleMode() {
    isLogin.value = !isLogin.value
    email.value = ''
    confirmPassword.value = ''
    captchaText.value = ''
    agreedTerms.value = false
    showTermsDialog.value = false
    if (!isLogin.value) {
      refreshCaptcha()
    }
  }
  ```

- [ ] **Step 4：修改 `handleSubmit()` — 注册时检查勾选状态**

  找到 `handleSubmit` 函数内校验验证码之后、`loading.value = true` 之前的位置：
  ```js
    if (!captchaText.value.trim()) {
      alert(t('请输入验证码'))
      return
    }
  }
  ```

  在这段 `}` 闭合之后（即整个 `if (!isLogin.value)` 块之后），插入：
  ```js
  if (!isLogin.value && !agreedTerms.value) {
    showTermsDialog.value = true
    return
  }
  ```

- [ ] **Step 5：修改 `handleSubmit()` — 注册调用时传入 agreed 参数**

  找到：
  ```js
      const result = isLogin.value
        ? await login(username.value.trim(), password.value)
        : await register(username.value.trim(), password.value, email.value.trim(), captchaId.value, captchaText.value.trim())
  ```
  改为：
  ```js
      const result = isLogin.value
        ? await login(username.value.trim(), password.value)
        : await register(username.value.trim(), password.value, email.value.trim(), captchaId.value, captchaText.value.trim(), agreedTerms.value)
  ```

- [ ] **Step 6：新增 `agreeAndSubmit()` 函数**

  在 `handleSubmit` 函数之后添加：
  ```js
  function agreeAndSubmit() {
    agreedTerms.value = true
    showTermsDialog.value = false
    handleSubmit()
  }
  ```

- [ ] **Step 7：在 `<style scoped>` 末尾追加样式**

  ```css
  .agree-row {
    margin-bottom: 12px;
  }
  .agree-label {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    cursor: pointer;
    color: var(--color-text);
    font-size: 14px;
    line-height: 1.5;
  }
  .agree-checkbox {
    margin-top: 2px;
    width: 16px;
    height: 16px;
    accent-color: var(--color-primary);
    flex-shrink: 0;
    cursor: pointer;
  }
  .agree-link {
    color: var(--color-primary);
    text-decoration: underline;
    cursor: pointer;
  }
  .terms-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 200;
  }
  .terms-dialog {
    background: var(--color-card);
    border: 1px solid var(--color-border);
    border-radius: 8px;
    padding: 24px;
    max-width: 320px;
    width: 88%;
  }
  .terms-dialog-title {
    color: var(--color-primary);
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 12px;
    text-align: center;
  }
  .terms-dialog-body {
    color: var(--color-text);
    font-size: 15px;
    line-height: 1.7;
    margin-bottom: 20px;
    text-align: center;
  }
  .terms-dialog-btns {
    display: flex;
    gap: 12px;
  }
  .btn-cancel {
    flex: 1;
    height: 44px;
    background: transparent;
    color: var(--color-text-secondary);
    border: 1px solid var(--color-border);
    border-radius: 4px;
    font-size: 15px;
    cursor: pointer;
  }
  .btn-agree {
    flex: 1;
    height: 44px;
    font-size: 15px;
  }
  ```

- [ ] **Step 8：前端验证整体流程**

  访问 `http://localhost:3000/login`，切换到注册模式，验证以下场景：

  1. **未勾选直接点注册** → 弹出"温馨提示"弹窗，包含协议链接和"同意并注册"按钮
  2. **弹窗点"取消"** → 弹窗关闭，勾选框仍为未勾选
  3. **弹窗点"同意并注册"** → 勾选框变为勾选，继续执行注册逻辑（填完其他字段后才会真正提交）
  4. **已勾选直接点注册** → 不弹窗，直接执行注册逻辑
  5. **点击《用户协议与隐私政策》链接** → 跳转到 `/terms-privacy` 页面，不触发勾选

- [ ] **Step 9：提交**

  ```bash
  git add frontend/src/views/Login.vue
  git commit -m "feat: add terms agreement checkbox and confirm dialog to registration"
  ```

---

## 验收清单

- [ ] 注册时不传 `agreed: true`，后端返回 400 + 中文错误信息
- [ ] 注册成功后，数据库中该用户的 `agreed_version`、`agreed_at`、`agreed_ip` 均有值
- [ ] 注册表单未勾选 → 弹出确认弹窗
- [ ] 弹窗"同意并注册"自动勾选并继续提交
- [ ] 勾选框文字中的链接跳转到协议页面，不干扰勾选状态
- [ ] 协议页面两部分内容完整，末尾有模板声明
- [ ] 设置页可通过"用户协议与隐私政策"菜单项跳转
- [ ] 登录模式下勾选框不显示
- [ ] 切换注册→登录→注册后，勾选状态重置为未勾选
