# 部署指南 — 六爻解卦

## 服务器环境要求

- Ubuntu Linux
- Python 3.8+
- Node.js 18+（Vite 5 要求）
- npm

## 首次部署

1. 将项目代码上传到服务器（如 `/home/ubuntu/web`）

2. 执行一键安装：

```bash
bash deploy.sh --setup
```

该命令会自动完成：
- 创建 Python 虚拟环境（`.venv/`）
- 安装 Python 依赖（`requirements.txt`）
- 安装前端依赖并构建（`npm install && npm run build`）
- 注册 systemd 服务（`liuyao.service`）
- 启动服务

3. 验证服务状态：

```bash
sudo systemctl status liuyao
```

## 日常更新部署（零停机）

更新代码后，执行：

```bash
bash deploy.sh
```

该命令会：
- 自动备份数据库（`backups/users.db.YYYYMMDD_HHMMSS`，保留最近 10 份）
- 更新 Python 依赖
- 重新构建前端
- 平滑重启 Gunicorn（`systemctl reload`，旧进程处理完当前请求后退出，用户无感知）
- 重启时 `init_db()` 自动执行数据库迁移（新增字段、新增表）

## 常用运维命令

```bash
# 查看服务状态
sudo systemctl status liuyao

# 查看实时日志
sudo journalctl -u liuyao -f

# 手动平滑重启（不重新构建）
sudo systemctl reload liuyao

# 完全停止服务
sudo systemctl stop liuyao

# 启动服务
sudo systemctl start liuyao

# 强制重启（会中断当前请求，非必要不用）
sudo systemctl restart liuyao
```

## 架构说明

```
Gunicorn (master)
  └── Worker (1 worker, 4 threads, gthread 模式)
        ├── Flask app (gua_app:app)
        ├── DialogManager (会话缓存)
        └── _async_tasks (异步任务字典)
```

使用 1 worker + 4 线程的原因：
- `_async_tasks` 异步任务字典在内存中，多 worker 会导致提交和轮询落到不同进程
- `DialogManager` 会话缓存在内存中，多 worker 会导致会话丢失
- 4 线程足以处理并发请求

## 平滑重启原理

`systemctl reload` 发送 `HUP` 信号给 Gunicorn master：

```
reload 前:   Master ─── Worker(旧代码，正在处理用户请求)

reload 时:   Master ─── Worker(旧代码，继续处理完当前请求...)
                    └── Worker(新代码，接收新请求)

几秒后:      Master ─── Worker(新代码)
```

`gunicorn.conf.py` 中 `graceful_timeout = 300`，旧 worker 最多等 5 分钟处理完当前 LLM 请求后才退出。

## 数据库迁移

`users.db` 是运行时数据，**不在代码仓库中**（已被 `.gitignore` 排除），部署时不会被覆盖。

### 迁移机制

所有数据库迁移代码在 `auth.py` 的 `init_db()` 函数中，Gunicorn 启动/重启时自动执行。

**新增字段** — 在 `init_db()` 中追加 `ALTER TABLE ADD COLUMN`，用 `try/except` 包裹：

```python
# 数据库迁移：添加 xxx 字段
try:
    db.execute("ALTER TABLE users ADD COLUMN xxx TEXT")
    db.commit()
except Exception:
    pass  # 列已存在
```

**新增表** — 使用 `CREATE TABLE IF NOT EXISTS`：

```python
db.execute('''CREATE TABLE IF NOT EXISTS new_table (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ...
)''')
```

部署后 Gunicorn 重启，`init_db()` 自动运行，新字段/新表就会被创建。已存在的则静默跳过。

### 备份与回滚

`deploy.sh` 每次部署前自动备份数据库到 `backups/` 目录，保留最近 10 份。

如需手动回滚：

```bash
# 停止服务
sudo systemctl stop liuyao

# 恢复备份
cp backups/users.db.20260417_190000 users.db

# 启动服务
sudo systemctl start liuyao
```

### 注意事项

SQLite 的 `ALTER TABLE` 只支持 **ADD COLUMN**，不支持删除列、重命名列、修改列类型。如需这类操作，需要：

1. 创建新表
2. 迁移数据：`INSERT INTO new_table SELECT ... FROM old_table`
3. 删除旧表：`DROP TABLE old_table`
4. 重命名新表：`ALTER TABLE new_table RENAME TO old_table`

这类破坏性迁移建议先在本地测试，确认无误后再部署。

## 崩溃自动重启与日志排查

### 自动重启

`liuyao.service` 中配置了 `Restart=on-failure`，服务异常崩溃时 systemd 会在 5 秒后自动重启。手动执行 `systemctl stop` 不会触发自动重启。

### 查看日志

```bash
# 查看最近的日志（最后 100 行）
sudo journalctl -u liuyao -n 100

# 查看实时日志（类似 tail -f）
sudo journalctl -u liuyao -f

# 查看今天的日志
sudo journalctl -u liuyao --since today

# 查看某个时间段的日志
sudo journalctl -u liuyao --since "2026-04-17 18:00" --until "2026-04-17 20:00"
```

### 崩溃日志特征

崩溃重启时，日志中会出现类似以下内容：

```
liuyao.service: Main process exited, code=exited, status=1/FAILURE
liuyao.service: Failed with result 'exit-code'.
liuyao.service: Scheduled restart job, restart counter is at 1.
liuyao.service: Started Liuyao AI Divination (Gunicorn).
```

Python 的 traceback 堆栈信息也会被 journalctl 捕获，可以直接定位崩溃原因。

### 停止与禁用服务

```bash
# 停止服务（不触发自动重启）
sudo systemctl stop liuyao

# 永久禁用（停止 + 开机不自启）
sudo systemctl stop liuyao
sudo systemctl disable liuyao

# 恢复启用
sudo systemctl enable liuyao
sudo systemctl start liuyao
```

## 关键配置文件

| 文件 | 说明 |
|------|------|
| `gunicorn.conf.py` | Gunicorn 配置（端口、线程、超时、SSL） |
| `deploy/liuyao.service` | systemd 服务模板（首次安装时自动应用） |
| `deploy.sh` | 部署脚本 |
| `.env` | 环境变量（API Key 等，不要提交到代码仓库） |

## SSL 证书

将证书文件放到项目根目录下的 `certs/` 目录：

```
certs/
  ├── cert.pem
  └── key.pem
```

Gunicorn 启动时会自动检测并启用 HTTPS。
