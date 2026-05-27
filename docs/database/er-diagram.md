# ER 关系说明（文字版，V1.1）

## 核心关系

- `users` 1:N `profiles`
- `users` 1:N `refresh_tokens`
- `profiles` 1:N `profile_drafts`
- `profiles` 1:N `review_requests`
- `profiles` 1:N `achievements`
- `profile_drafts` 1:N `review_requests`
- `users` 1:N `media_assets`
- `profile_drafts` N:M `media_assets`，通过 `profile_draft_files` 关联

## 验证码关系

- `verification_codes` 不强制外键关联 `users`。
- 业务层通过 `channel + target + purpose` 查找和校验验证码。
- 验证码只保存 `code_hash`，不保存明文。

## 草稿与审核流关系

1. 用户保存资料草稿，写入 `profile_drafts`。
2. 每次保存形成新的 `version_no`，同一 `profile_id` 通过部分唯一索引保证仅一个 `is_latest = 1`。
3. 用户提交审核，生成 `review_requests`，状态为 `pending`。
4. `review_requests.draft_id` 指向提交时的草稿版本，用于冻结和追溯审核快照。
5. 同一 `profile_id` 通过部分唯一索引保证仅一个 `pending` 审核任务。
6. 管理员审核后将 `review_requests.status` 更新为 `approved` 或 `rejected`。
7. 审核通过后由服务层将 `change_payload` 发布到 `profiles` 和 `achievements`。
8. `profiles.published_version_no` 记录当前发布的草稿版本号。

## 证明材料关系

1. 上传文件元数据写入 `media_assets`。
2. 文件二进制不进入数据库，只保存路径、MIME、大小、校验值等元数据。
3. 草稿证明材料通过 `profile_draft_files(draft_id, media_asset_id)` 建立关联。
4. `media_assets.ref_type/ref_id` 作为 V1 兼容字段保留，新代码不依赖该字段表达草稿证明材料。
5. 文件删除采用 `media_assets.deleted_at` 软删除，草稿读取时过滤已删除文件。

## 状态边界

- `profile_drafts.review_status`：`draft` / `pending` / `approved` / `rejected`
- `review_requests.status`：`pending` / `approved` / `rejected`

说明：`draft` 是草稿状态，不是审核任务状态，因此不得写入 `review_requests.status`。

## 约束建议

- 外键在数据库层与业务层双重校验。
- 用户建议软删除，避免审核链断裂。
- 历史草稿与历史审核记录原则上不物理删除，满足审计追溯。
- `users.email` 当前仍保持 V1 的 `NOT NULL` 约束；若产品确认支持纯手机号注册，需要单独迁移并同步更新 API 与数据库文档。
