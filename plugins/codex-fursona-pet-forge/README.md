# Codex Fursona Pet Forge

Codex Fursona Pet Forge 是一個 Codex marketplace plugin，主功能是協助使用者用一張 fursona 或角色設定圖製作 Codex 桌寵造型。陪伴功能是輔助：使用者可以設定桌寵怎麼稱呼自己、桌寵自己的名字與性格、保存少量非敏感記憶，並設定溫和的起身活動提醒。

拉爾夫是內建 guide 與範例桌寵，不是使用者必須永久採用的人格或外觀。使用者可以先用拉爾夫協助製作自己的 pet skin，也可以之後再調整 Codex pet 的名字、語氣和背景設定。

MVP 不寫 `AGENTS.override.md`，也不依賴 post-install hook。第一次可執行的 `SessionStart` 會 init-on-read 建立資料檔。

## 功能定位

### 主要：桌寵造型生成

- 用一張 fursona / 角色設定圖建立 Codex desktop pet package。
- 支援 `/goal` 一鍵流程：產生 base、各動作 row、QA 預覽、atlas、package 和 final report。
- 支援 supervised mode：一個動作一個動作慢慢做，每個 row 都用透明 192x208 GIF 讓使用者確認；速度較慢，但通常更穩。
- 依賴外部 `hatch-pet` skill 做正式產圖、抽格、QA media、atlas 組裝和 package 驗證。
- `generate2dsprite` 只作為選配，不是必要依賴。

### 輔助：陪伴與提醒

- `remember-this`：保存穩定、長期有用、非敏感的使用者偏好，例如稱呼、互動偏好。
- `setup-action`：用 dry-run 與 confirm token 執行少量白名單設定。
- `stretch-reminder`：準備起身、喝水、伸展等 Codex thread automation 提醒。
- persona 設定：使用者可以調整桌寵名稱、語氣、性格、背景與互動邊界。

提醒功能不監控作業系統活動，不記錄鍵盤、滑鼠、前景 app、視窗標題、網址、截圖、相機或麥克風。時間感知文案只做溫和推測，例如早上說早安、中午問「是去吃飯了嗎？」、午夜後問「是不是該睡了？」。

## 安裝

在 repo 根目錄外或任意位置執行：

```bash
codex plugin marketplace add /path/to/codex-fursona-pet-forge
codex plugin add codex-fursona-pet-forge@codex-fursona-local
```

本地 checkout 還沒改資料夾名稱前，請使用實際 checkout 路徑：

```bash
codex plugin marketplace add /path/to/local/checkout
codex plugin add codex-fursona-pet-forge@codex-fursona-local
```

若 Codex 顯示 hooks 需要 review，請在 Codex 裡開 `/hooks`，檢查 `codex-fursona-pet-forge` 的 `SessionStart` 與 `Stop` hooks，確認 command 指向 plugin cache 內的：

- `python3 ${PLUGIN_ROOT}/hooks/session_start.py`
- `python3 ${PLUGIN_ROOT}/hooks/stop.py`

確認後 trust hooks，再開新 session。

安裝後新 session 應能載入下列 plugin skills：

- `make-pet-skin`
- `pet-generation-handoff`
- `remember-this`
- `setup-action`
- `stretch-reminder`

若 persona 文字有出現，但 Codex 無法使用這些 skills，請確認安裝到 cache 的 `.codex-plugin/plugin.json` 包含 `"skills": "./skills/"`，且每個 `SKILL.md` 都含有 `name` 與 `description` frontmatter。更新本地 plugin 後請 bump version 或重新安裝，避免 Codex 繼續讀舊 cache。

### 外部產圖 skill

正式產圖需要 OpenAI curated skills repo 裡的 `hatch-pet`：

```text
https://github.com/openai/skills/tree/main/skills/.curated/hatch-pet
```

給新手使用時，可以直接請 Codex 幫忙：

```text
Install the hatch-pet skill from https://github.com/openai/skills/tree/main/skills/.curated/hatch-pet
```

Codex 應使用 `skill-installer` 將 `hatch-pet` 安裝到使用者的 Codex skills 目錄。安裝完成後，請 Restart Codex，讓新 skill 被載入。

### 本地圖片處理依賴

在用 `/goal` 測完整桌寵產圖前，建議先在 repo 根目錄安裝專案依賴：

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
```

這會安裝 `Pillow`，提供本地 QA 腳本需要的 `PIL` 模組，用來讀寫 PNG/WebP/GIF、清透明背景、裁切 sprites、做 contact sheet 與像素級檢查。

## 製作桌寵造型

一般入口：

```text
用這張角色設定圖幫我做 Codex 桌寵。
```

若要測試一鍵完成流程，可以使用 `/goal` 要求一次完成：

```text
/goal 用這張角色設定圖一鍵製作完整 Codex 桌寵，包含所有動作、QA、atlas 和 package。
```

若想提高穩定度，可以要求一個動作一個動作做：

```text
用這張角色設定圖幫我做 Codex 桌寵，但一個動作一個動作慢慢做，每個 GIF 讓我確認。
```

`make-pet-skin` skill 會先做 preflight。正式產圖需要外部 `hatch-pet` skill；如果尚未安裝，skill 會在開始前停下來請你安裝：

```text
Install the hatch-pet skill from https://github.com/openai/skills/tree/main/skills/.curated/hatch-pet
```

安裝後需要 Restart Codex。`generate2dsprite` 是推薦選配，不是必要依賴。

從 repo 根目錄看的完整流程參考：

- `../../docs/pet-skin-workflow.md`
- `../../docs/pet-skin-action-defaults.md`
- `../../docs/pet-skin-quality-checklist.md`
- `../../docs/pet-package-spec.md`

## 起身提醒

`stretch-reminder` skill 可以準備起身活動提醒設定，並產生 Codex thread automation 需要的名稱、排程與 prompt。

開始：

```text
拉爾夫，每 50 分鐘提醒我起身活動 3 分鐘。
```

暫停、恢復、停止或查狀態：

```text
暫停起身提醒。
恢復起身提醒。
停止起身提醒。
目前起身提醒狀態？
```

提醒使用 Codex App thread automations 做排程；plugin hooks 本身不是計時器。若目前 Codex surface 無法建立 automation，skill 只會更新/回報本地設定，不會假裝提醒已排程成功。

## 停用

單次 session 或 subprocess：

```bash
CODEX_PET_DISABLE=1 codex
CODEX_PET_DISABLE=1 codex exec "..."
```

Repo marker fallback：

```text
<cwd>/.codex-pet-disable
```

若 hook environment 沒繼承 env var，cwd marker 仍會讓 `SessionStart` 與 `Stop` short-circuit。也可以在 Codex `/hooks` 停用相關 hook，或在 Codex plugin 設定中停用整個 plugin。

## Locale

第一次 `SessionStart` 建立 `persona.yaml` 時，可用 `CODEX_PET_LOCALE` 選擇預設 persona 語言：

```bash
CODEX_PET_LOCALE=zh-TW codex
CODEX_PET_LOCALE=en codex
```

目前內建：

- `zh-TW`：`personas/default-ralf.zh-TW.yaml`
- `en`：`personas/default-ralf.en.yaml`

若未設定或指定未知 locale，會 fallback 到 `zh-TW`。若已建立 `$PLUGIN_DATA/persona.yaml`，之後改 `CODEX_PET_LOCALE` 不會覆寫使用者已自訂的人格檔；請手動編輯或刪除既有 `persona.yaml` 後重新初始化。

## 資料路徑

正式 plugin runtime 優先使用 Codex 提供的 `PLUGIN_DATA`：

```text
$PLUGIN_DATA/
├── persona.yaml
├── config.yaml
├── .onboarding-pending
├── personal-facts/
│   ├── MEMORY.md
│   └── *.md
├── recent/
│   └── *.md
├── markers/
│   └── *.pending
└── logs/
    ├── error.log
    └── digest.log
```

若 skill 或手動執行時沒有 `PLUGIN_DATA`，會先讀 `$CODEX_HOME/config.toml`
裡已啟用的 plugin selector，例如 `codex-fursona-pet-forge@codex-fursona-local`，並推導到：

```text
$CODEX_HOME/plugins/data/codex-fursona-pet-forge-codex-fursona-local/
```

為了保留改名前的本地資料，若找不到新路徑，resolver 仍會嘗試讀取 pre-rename managed data 或 legacy data。只有找不到 Codex managed plugin data 時，才 fallback 到新 runtime 路徑：

```text
$CODEX_HOME/plugins/codex-fursona-pet-forge/data/
```

## 記憶模型

- `persona.yaml`：使用者可編輯的人格設定；下次 `SessionStart` 生效。
- `personal-facts/MEMORY.md`：長期、非敏感 personal facts 的索引。
- `personal-facts/*.md`：單一 fact 檔，由 `remember-this` skill 寫入。
- `recent/*.md`：Stop hook 背景 digest 的短期延續摘要，只保留最新 3 個。

Stop hook 是 turn-scope，不是真正的 session exit。Digest 是 best-effort：parse 失敗、LLM/子程序失敗或 transcript schema 改變時，只寫 log，不阻塞 Codex。

## Persona Threat Model

`persona.yaml` 是 trusted local instruction content，但仍做基本防護：

- loader 檢查必填欄位、長度上限與控制字元。
- `SessionStart` 只從解析出的 plugin data 目錄讀 persona、facts、recent，不讀任意路徑。
- persona flavor 不可凌駕 Codex safety、coding accuracy 或使用者明確指令。
- 拉爾夫不能宣稱記得未出現在 Personal facts 或 Recent talk 的內容。
- `remember-this` 預設拒寫 token、password、API key 等疑似敏感內容，除非使用者明確要求本機保存並傳入 override。
- `setup-action` 對寫入動作強制 dry-run、confirm token、固定白名單 target，並拒絕 symlink target。

## 開發驗證

```bash
.venv/bin/python -m pytest -q
```
