---
name: remember-this
description: Persist stable, non-sensitive personal facts about the user for future Codex Fursona Pet Forge sessions.
---

# remember-this

當使用者明確透露穩定、長期有用、非敏感的個人事實時，使用這個 skill 保存到本機 personal facts。

適合保存：

- 使用者偏好稱呼。
- 長期互動偏好，例如喜歡一步一步確認、不喜歡被反覆追問。
- 使用者明確希望拉爾夫記住的非敏感背景。

不要保存：

- 密碼、API token、金鑰、私密健康或財務細節。
- 只有當下任務才有用的工程事實；這類內容交給 Codex native memories 或專案文件。

寫入方式：

```bash
python3 ${PLUGIN_ROOT}/skills/remember-this/write_fact.py
```

stdin JSON 範例：

```json
{
  "name": "preferred-name",
  "fact": "使用者喜歡被叫做小雅。",
  "type": "identity",
  "sensitivity": "normal",
  "source": "conversation"
}
```

若內容疑似敏感，預設會拒寫。只有在使用者明確要求本機保存，且你判斷適合保存時，才傳入 `"allow_sensitive": true`。
