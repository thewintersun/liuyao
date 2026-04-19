# 邀请好友得额度 — 技术文档

## 功能概述

注册用户可通过分享邀请链接获得额度，同时为应用带来新用户。

## 奖励规则

| 触发条件 | 邀请人获得 | 被邀请人获得 |
|---------|-----------|-------------|
| 游客点开邀请链接 | +5 次 | 无 |
| 被邀请人注册成功 | +20 次 | +20 次 |

### 防刷策略

- 同一 IP 24h 内最多触发 3 次"链接访问"奖励
- 每用户每自然月最多邀请 20 人（游客访问 + 注册合计）
- 所有奖励数值可在管理后台 `系统设置` 页面修改

## 数据库表结构

### users 表新增字段

| 字段 | 类型 | 说明 |
|------|------|------|
| invite_code | TEXT | 用户唯一邀请码（6位大写字母+数字） |
| invited_by | INTEGER | 邀请人的 user_id |

### invite_records 表（新建）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增 |
| inviter_id | INTEGER FK | 邀请人 user_id |
| type | TEXT | 'visit' 或 'register' |
| visitor_ip | TEXT | 访客 IP（visit 类型） |
| invitee_id | INTEGER | 被邀请注册的用户 ID（register 类型） |
| reward | INTEGER | 邀请人获得的额度 |
| created_at | TIMESTAMP | 记录创建时间 |

## API 端点

### POST /api/invite/visit

游客访问邀请链接时调用，无需认证。

**请求体：**
```json
{ "code": "A3K9F2" }
```

**响应：**
```json
{ "status": "success" }
```

### GET /api/invite/stats

获取当前用户的邀请统计，需要认证。

**响应：**
```json
{
  "status": "success",
  "invite_code": "A3K9F2",
  "monthly_count": 3,
  "monthly_reward": 35,
  "monthly_limit": 20,
  "total_count": 15,
  "total_reward": 200,
  "records": [
    {
      "type": "register",
      "visitor_ip": null,
      "invitee_name": "user123",
      "reward": 20,
      "created_at": "2026-04-19 10:30:00"
    }
  ]
}
```

### GET /api/config/quota（扩展）

返回值新增：
- `invite_visit_reward`: 访问链接奖励
- `invite_register_reward`: 注册奖励（邀请人）
- `invite_register_bonus`: 注册奖励（被邀请人）

### POST /api/auth/register（扩展）

请求体新增可选参数 `invite_code`。

## 管理后台配置项

| 配置 key | 默认值 | 说明 |
|----------|--------|------|
| INVITE_VISIT_REWARD | 5 | 访问链接奖励 |
| INVITE_REGISTER_REWARD | 20 | 注册奖励（邀请人） |
| INVITE_REGISTER_BONUS | 20 | 注册奖励（被邀请人） |
| INVITE_MONTHLY_LIMIT | 20 | 每月邀请人数上限 |
| INVITE_IP_DAILY_LIMIT | 3 | 同IP每日访问上限 |

## 前端流程

1. **邀请链接检测**：App.vue 在 onMounted 中检测 URL 的 `?ref=CODE` 参数
   - 存入 sessionStorage
   - 调用 POST /api/invite/visit 通知后端
   - history.replaceState 清除 URL 参数

2. **注册页**：Login.vue 注册表单新增邀请码输入框
   - 从 sessionStorage 自动填入
   - 注册成功后清除 sessionStorage

3. **邀请页面**：/invite 路由，展示邀请码、链接、统计、记录

4. **额度用完引导**：Analysis.vue
   - 游客：引导注册（原逻辑不变）
   - 已登录用户：弹窗引导到邀请页面

## 修改文件清单

| 文件 | 操作 |
|------|------|
| config.py | 新增 5 个常量 |
| auth.py | 迁移 + 新函数 + 修改 register_user |
| admin_service.py | defaults + get_all_configs 新增 5 key |
| gua_app.py | 2 个新端点 + 修改 register/quota |
| frontend/src/api/index.js | 3 个新函数 + 修改 register |
| frontend/src/App.vue | URL ref 参数检测 |
| frontend/src/views/Login.vue | 注册表单加邀请码 |
| frontend/src/views/Invite.vue | 新建 |
| frontend/src/views/Settings.vue | 加邀请入口 |
| frontend/src/views/Analysis.vue | 登录用户额度用完弹窗 |
| frontend/src/views/admin/SystemConfig.vue | 邀请配置区块 |
| frontend/src/router/index.js | 加路由 |
| frontend/src/components/NavBar.vue | titleMap |
