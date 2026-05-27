# 核心表结构（V1.1）

以下结构基于 SQLite + SQLAlchemy + Alembic 设计。当前 V1.1 在 V1 基础上做兼容扩展，保留既有表名、主键、核心外键与核心枚举语义。最终以迁移脚本为准：

- `backend/alembic/versions/08f4723ba902_init_schema_v1.py`
- `backend/alembic/versions/202605260001_expand_schema_v1_1.py`

## 设计约束

- SQLite 下枚举使用 `TEXT + CHECK`。
- 复杂结构使用 `TEXT` 保存 JSON 字符串，由服务层负责序列化、反序列化与结构校验。
- 上传文件只保存路径与元数据，不保存二进制文件本体。
- 草稿状态与审核任务状态分离：`profile_drafts.review_status` 可为 `draft/pending/approved/rejected`，`review_requests.status` 仅允许 `pending/approved/rejected`。
- 审核链路可追溯：草稿、审核请求、审核结果和发布版本通过 `profile_drafts.id`、`review_requests.draft_id`、`profiles.published_version_no` 关联。
- `users.email` 当前仍按 V1 保持 `NOT NULL`；若后续确认支持纯手机号注册，需要单独重建表并增加 `CHECK(email IS NOT NULL OR phone IS NOT NULL)`。

## users

| 字段名 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | INTEGER | PK, AUTOINCREMENT | 用户 ID |
| email | TEXT | UNIQUE, NOT NULL | 登录邮箱；当前 V1 兼容要求仍非空 |
| phone | TEXT | UNIQUE, NULL | 手机号 |
| password_hash | TEXT | NOT NULL | 密码哈希 |
| display_name | TEXT | NOT NULL | 展示名，对应 API `User.name` |
| avatar_url | TEXT | NULL | 头像 URL |
| role | TEXT | NOT NULL, CHECK `member/admin` | 用户角色 |
| status | TEXT | NOT NULL, CHECK `active/disabled` | 用户状态 |
| created_at | DATETIME | NOT NULL | 创建时间，按 UTC 写入 |
| updated_at | DATETIME | NOT NULL | 更新时间，按 UTC 写入 |

索引：

- `uq_users_email`：唯一约束，`email`
- `uq_users_phone`：唯一约束，`phone`
- `ix_users_display_name`：`display_name`
- `ix_users_role_status`：`role, status`

## verification_codes

| 字段名 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | INTEGER | PK, AUTOINCREMENT | 验证码记录 ID |
| channel | TEXT | NOT NULL, CHECK `email/sms` | 发送渠道 |
| target | TEXT | NOT NULL | 邮箱地址或手机号 |
| purpose | TEXT | NOT NULL, CHECK `register/login/reset_password` | 验证码用途 |
| code_hash | TEXT | NOT NULL | 验证码哈希，不保存明文 |
| expires_at | DATETIME | NOT NULL | 过期时间 |
| consumed_at | DATETIME | NULL | 使用时间 |
| attempt_count | INTEGER | NOT NULL, DEFAULT 0 | 校验尝试次数 |
| request_ip | TEXT | NULL | 请求 IP，安全日志辅助 |
| user_agent | TEXT | NULL | User-Agent，安全日志辅助 |
| created_at | DATETIME | NOT NULL | 创建时间，按 UTC 写入 |

索引：

- `ix_verification_codes_expires_at`：`expires_at`
- `ix_verification_codes_target_purpose_created_at`：`target, purpose, created_at`

## refresh_tokens

| 字段名 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | INTEGER | PK, AUTOINCREMENT | 刷新令牌记录 ID |
| user_id | INTEGER | FK -> users.id, NOT NULL | 用户 ID |
| token_hash | TEXT | UNIQUE, NOT NULL | 刷新令牌哈希；明文 token 仅响应时返回一次 |
| expires_at | DATETIME | NOT NULL | 过期时间 |
| revoked_at | DATETIME | NULL | 撤销时间 |
| last_used_at | DATETIME | NULL | 最近使用时间 |
| created_ip | TEXT | NULL | 创建 IP |
| user_agent | TEXT | NULL | User-Agent |
| created_at | DATETIME | NOT NULL | 创建时间，按 UTC 写入 |

索引：

- `uq_refresh_tokens_token_hash`：唯一约束，`token_hash`
- `ix_refresh_tokens_user_expires_at`：`user_id, expires_at`

## profiles

| 字段名 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | INTEGER | PK, AUTOINCREMENT | 资料 ID |
| user_id | INTEGER | FK -> users.id, NOT NULL | 用户外键 |
| headline | TEXT | NULL | 一句话简介，当前 API 未强制返回 |
| bio | TEXT | NULL | 已发布个人简介 |
| major_tags | TEXT | NULL | 标签 JSON 字符串 |
| visibility | TEXT | NOT NULL, CHECK `public/internal` | 资料可见性 |
| published_version_no | INTEGER | NOT NULL, DEFAULT 0 | 当前已发布草稿版本号 |
| created_at | DATETIME | NOT NULL | 创建时间，按 UTC 写入 |
| updated_at | DATETIME | NOT NULL | 更新时间，按 UTC 写入 |

索引：

- `ix_profiles_user_id`：`user_id`
- `ix_profiles_updated_at`：`updated_at`
- `ix_profiles_visibility_updated_at`：`visibility, updated_at`

## profile_drafts

| 字段名 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | INTEGER | PK, AUTOINCREMENT | 草稿 ID |
| profile_id | INTEGER | FK -> profiles.id, NOT NULL | 关联资料 |
| editor_user_id | INTEGER | FK -> users.id, NOT NULL | 编辑者 |
| draft_content | TEXT | NOT NULL | 草稿完整 JSON 快照 |
| review_status | TEXT | NOT NULL, DEFAULT `draft`, CHECK `draft/pending/approved/rejected` | 草稿审核状态 |
| version_no | INTEGER | NOT NULL | 草稿版本号 |
| is_latest | BOOLEAN | NOT NULL, DEFAULT 1 | 是否当前最新草稿 |
| created_at | DATETIME | NOT NULL | 创建时间，按 UTC 写入 |
| updated_at | DATETIME | NOT NULL | 更新时间，按 UTC 写入 |

`draft_content` 建议结构：

```json
{
  "bio": "...",
  "experiences": [],
  "awards": []
}
```

索引与约束：

- `uq_profile_drafts_profile_version`：唯一，`profile_id, version_no`
- `ix_profile_drafts_editor_latest`：`editor_user_id, is_latest`
- `uq_profile_drafts_one_latest`：SQLite 部分唯一索引，`UNIQUE(profile_id) WHERE is_latest = 1`

## review_requests

| 字段名 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | INTEGER | PK, AUTOINCREMENT | 审核请求 ID |
| profile_id | INTEGER | FK -> profiles.id, NOT NULL | 关联资料 |
| draft_id | INTEGER | FK -> profile_drafts.id, NULL | 关联草稿版本；用于追溯审核快照 |
| submitter_user_id | INTEGER | FK -> users.id, NOT NULL | 提交者 |
| reviewer_user_id | INTEGER | FK -> users.id, NULL | 审核者 |
| status | TEXT | NOT NULL, DEFAULT `pending`, CHECK `pending/approved/rejected` | 审核任务状态；不允许 `draft` |
| change_payload | TEXT | NOT NULL | 提交审核时冻结的草稿 JSON 快照 |
| review_comment | TEXT | NULL | 审核通过备注 |
| reject_reason | TEXT | NULL | 驳回原因 |
| submitted_at | DATETIME | NOT NULL | 提交时间，按 UTC 写入 |
| reviewed_at | DATETIME | NULL | 审核完成时间，按 UTC 写入 |
| updated_at | DATETIME | NOT NULL | 更新时间，按 UTC 写入 |

索引与约束：

- `ix_review_requests_status_submitted_at`：`status, submitted_at`
- `ix_review_requests_reviewer_status`：`reviewer_user_id, status`
- `uq_review_requests_one_pending`：SQLite 部分唯一索引，`UNIQUE(profile_id) WHERE status = 'pending'`

## achievements

| 字段名 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | INTEGER | PK, AUTOINCREMENT | 条目 ID |
| profile_id | INTEGER | FK -> profiles.id, NOT NULL | 关联资料 |
| category | TEXT | NOT NULL, CHECK `award/experience` | 条目类型 |
| title | TEXT | NOT NULL | 标题；奖项对应 API `AwardItem.name` |
| organization | TEXT | NULL | 履历组织，对应 API `ExperienceItem.organization` |
| description | TEXT | NULL | 描述 |
| start_date | DATE | NULL | 履历开始日期 |
| end_date | DATE | NULL | 履历结束日期 |
| award_level | TEXT | NULL | 奖项级别，对应 API `AwardItem.level` |
| award_year | INTEGER | NULL, CHECK `1900-2100` | 获奖年份 |
| happened_at | DATE | NULL | V1 兼容字段，通用发生日期 |
| sort_order | INTEGER | NOT NULL, DEFAULT 0 | 展示排序 |
| created_at | DATETIME | NOT NULL | 创建时间，按 UTC 写入 |
| updated_at | DATETIME | NOT NULL | 更新时间，按 UTC 写入 |

索引：

- `ix_achievements_title`：`title`
- `ix_achievements_profile_category`：`profile_id, category`
- `ix_achievements_profile_id_happened_at`：`profile_id, happened_at`
- `ix_achievements_award_keyword`：`category, title, award_level`

## media_assets

| 字段名 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | INTEGER | PK, AUTOINCREMENT | 文件记录 ID |
| owner_user_id | INTEGER | FK -> users.id, NOT NULL | 上传者 |
| file_name | TEXT | NOT NULL | 原始文件名 |
| file_path | TEXT | UNIQUE, NOT NULL | 存储路径 |
| file_type | TEXT | NOT NULL | MIME 类型 |
| file_size | INTEGER | NOT NULL, CHECK `file_size > 0` | 文件大小，单位字节 |
| ref_type | TEXT | NULL, CHECK `NULL/profile/review` | V1 兼容字段；新证明材料关联使用 `profile_draft_files` |
| ref_id | INTEGER | NULL | V1 兼容字段 |
| checksum_sha256 | TEXT | NULL | 文件校验值 |
| deleted_at | DATETIME | NULL | 软删除时间 |
| created_at | DATETIME | NOT NULL | 上传时间，按 UTC 写入 |

索引：

- `uq_media_assets_file_path`：唯一，`file_path`
- `ix_media_assets_deleted_at`：`deleted_at`
- `ix_media_assets_owner_created_at`：`owner_user_id, created_at`

## profile_draft_files

| 字段名 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| draft_id | INTEGER | FK -> profile_drafts.id, NOT NULL | 草稿 ID |
| media_asset_id | INTEGER | FK -> media_assets.id, NOT NULL | 文件 ID |
| created_at | DATETIME | NOT NULL | 关联创建时间，按 UTC 写入 |

主键：

- `pk_profile_draft_files`：`draft_id, media_asset_id`

索引：

- `ix_profile_draft_files_media_asset_id`：`media_asset_id`

## V1.1 迁移说明

V1.1 迁移为兼容扩展：

- 新增表：`verification_codes`、`refresh_tokens`、`profile_draft_files`。
- 增加字段：`users.avatar_url`、`profiles.published_version_no`、`profile_drafts.review_status/updated_at`、`review_requests.draft_id/reject_reason/updated_at`、`achievements` 履历/奖项扩展字段、`media_assets.file_name/checksum_sha256/deleted_at`。
- 放宽 `media_assets.ref_type/ref_id` 为可空，以兼容新证明材料关联方式。
- 使用 SQLite 表重建方式补充部分 NOT NULL、CHECK 与外键约束。
- `downgrade` 会恢复 V1 表结构，并将 V1.1 新增字段裁剪；回滚前必须备份数据库。
