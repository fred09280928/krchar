# Plan — KRChar（韓文 두벌식 打字練習表）

**Goal:** 一張「照著按就能打出正確字」的韓文練習表——每列是 `鍵位序列 → 字`，且只收錄韓文中實際會出現的字。
**Status:** SETTLED（2026-11-26 資料定案；表已凍結，驗證器只在日後改表時重跑）— 練習程式尚未開始

---

## 1. Core Pipeline

```
Google Sheet HermesLang / KRChar (A1:E)
        │  export
        ▼
data/KRChar.csv ──┬──► code/validate_krchar.py ──► 鍵位重算 → PASS / FAIL
                  │        (keys → jamo → 組字 → 比對 B 欄)
                  ├──► data/KRChar.json            （記錄格式）
                  └──► data/syllable-coverage.json （逐字出處）
```

## 2. Data Sources

| 來源 | 內容 | 用途 |
|---|---|---|
| Google Sheet **HermesLang** `1rMfAD58…Lfzk`，tab **KRChar** (`sheetId 1667330595`) | 833 列 × 5 欄 | 唯一真實來源（雲端） |
| `data/ko_full.txt.gz` — hermitdave/FrequencyWords 2018 ko | 688,129 詞形（OpenSubtitles） | 語料出處 |
| `data/kengdic.tsv.gz` — garfieldnate/kengdic | 133,765 條目 | 詞典出處 |
| `data/syllable-coverage.json` | 逐字：corpus_hits / corpus_words / in_corpus_or_dict；字母列 `kind: jamo` | 過濾依據、驗證交叉檢查 |

兩來源聯集 = 2,364 個音節。只用語料會誤刪 홰（횃불）、몌、좨 這類字幕罕見但詞典有的字。

## 3. Project Structure

```
KRChar/
├── planKRChar.md            # 本檔
├── README.md                # 專案說明、納入規則、更新步驟
├── code/
│   └── validate_krchar.py   # 鍵位重算驗證（stdlib only）
└── data/
    ├── KRChar.csv           # 833 列演練資料
    ├── KRChar.json          # 同資料，記錄格式
    ├── syllable-coverage.json
    ├── ko_full.txt.gz
    └── kengdic.tsv.gz
```

## 4. Schema

**`data/KRChar.csv`**：`category, Hangul, RR, Dubeolsik key, memo`

| 欄 | 說明 |
|---|---|
| `category` | `L0c` / `L0v` / `L0d` / `L1c` / `L1v` / `L1`–`L6`（見 §5.2） |
| `Hangul` | 單一字母或單一音節 |
| `RR` | Revised Romanization |
| `Dubeolsik key` | **實際按鍵序列**：小寫＝原鍵、大寫＝Shift（`R`=ㄲ、`W`=ㅉ、`O`=ㅒ、`P`=ㅖ）；無空格、無 `+`、無逗號 |
| `memo` | 目前全空（保留） |

**`data/syllable-coverage.json`**：`{ "<字>": {"kind":"syllable","corpus_hits":N,"corpus_words":N,"in_corpus_or_dict":bool} }`，字母列為 `{"kind":"jamo"}`。

## 5. Rules

### 5.1 鍵位（두벌식）

```
q ㅂ  w ㅈ  e ㄷ  r ㄱ  t ㅅ  y ㅛ  u ㅕ  i ㅑ  o ㅐ  p ㅔ
a ㅁ  s ㄴ  d ㅇ  f ㄹ  g ㅎ  h ㅗ  j ㅓ  k ㅏ  l ㅣ
z ㅋ  x ㅌ  c ㅊ  v ㅍ  b ㅠ  n ㅜ  m ㅡ
Shift 層（只有這 7 鍵）：Q ㅃ  W ㅉ  E ㄸ  R ㄲ  T ㅆ  O ㅒ  P ㅖ
```

- **ㅎ = `g`，ㅗ = `h`**（最常見的手工資料錯誤；`싫` 寫成 `tlfh` 會打出 실호）。
- **ㅒ／ㅖ 是單鍵** `O`／`P`；舊寫法 `Shift + o, i` 會多打一個 ㅑ，變成 얘야。
- 複合母音無單鍵，按成分依序輸入、由 IME 合併：ㅘ=`hk`、ㅙ=`ho`、ㅚ=`hl`、ㅝ=`nj`、ㅞ=`np`、ㅟ=`nl`、ㅢ=`ml`。
- 字母列單鍵即可（`r`=ㄱ）；音節列串接（`rk`=가、`Rnfg`=꿇、`ahrt`=몫）。

### 5.2 分類

| 分類 | 數 | 內容 |
|---|---|---|
| `L1c` | 13 | 會單獨打的子音：ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅎ（ㅋㅋㅋ、ㅇㅇ、ㄱㄱ、ㄹㅇ、ㅁㅊ、ㅅㄱ、ㅈㅅ、ㅂㅂ、ㄷㄷ、ㅊㅋ、ㅌㅌ） |
| `L1v` | 3 | 會單獨打的母音：ㅠㅠ、ㅜㅜ、ㅗ |
| `L0c` | 6 | 只在音節內用：ㄲㄸㅃㅆㅉㅍ |
| `L0v` | 7 | 只在音節內用：ㅏㅑㅓㅕㅛㅡㅣ |
| `L0d` | 11 | 複合母音／y 母音：ㅐㅒㅔㅖㅘㅙㅚㅝㅞㅟㅢ |
| `L1` | 10 | ㅇ＋基本母音（아 야 어 여 오 요 우 유 으 이） |
| `L2` | 11 | ㅇ＋ㅐ/ㅔ 系（애 얘 에 예 와 왜 외 워 웨 위 의） |
| `L3` | 174 | 初聲＋單母音（가 갸 거 겨 …） |
| `L4` | 155 | 初聲＋ㅐ/ㅔ/ㅒ/ㅖ（개 걔 게 계 …） |
| `L5` | 409 | 初聲＋母音＋收尾音（각 간 갈 감 …） |
| `L6` | 34 | 雙收尾音（몫 넋 앉 값 없 꿇 …） |

字母 40 列 + 音節 793 列 = **833**。字母列不套用「是否出現於韓文」的過濾（它們不是音節）。

### 5.3 納入規則

音節必須出現在 **語料或詞典任一**；兩邊都查不到的視為現代韓文不用。
頻率分層（僅供參考，不用於刪除）：常見 ≥1,000、偶見 100–999、少見 <100、詞典限定。

### 5.4 已移除（原始 884 → 833，共 51）

- 重複 1：`구`（L5 與 L3 重複，刪 L5 那列）
- L4 兩邊皆無 41：끠 냬 댸 뚸 뛔 럐 먜 뫠 믜 뱨 볘 붜 붸 뼤 뽸 뾔 뿨 쀄 쀠 쁴 싀 썌 쒜 즤 쪠 쮀 쯰 챼 쳬 촤 츼 컈 킈 턔 톄 톼 퍠 퐤 푀 풰 픠
- L3 兩邊皆無 4：꾜 뚀 뜌 뺘
- 僅存於古語／方言詞形 5：툐（교툐 표지）、퍄、몌（썅몌）、좨（좨치다）、훙（허훙）
- 保留的詞典限定字：홰（홰치다、횃불）

### 5.5 鍵位修正紀錄（9 格）

`삯 tkr→tkrt`、`많 dksg→aksg`、`읽 dlf→dlfr`、`얇 dlfq→difq`、`싫 tlfh→tlfg`、`잃 dlfh→dlfg`、`끓 RmfG→Rmfg`、`뚫 EnfG→Enfg`、`꿇 RnfG→Rnfg`；另 rows 2–62 標記法由 `Shift + r`／`d + h + k` 統一改為 `R`／`dhk`。

### 5.6 memo 欄（記憶法）

E 欄是提示欄，格式 `<圖像詞> = <鍵位>`（大寫＝Shift）：

| 鍵 | 圖像 | 鍵 | 圖像 | 鍵 | 圖像 | 鍵 | 圖像 |
|---|---|---|---|---|---|---|---|
| a | apple | b | ball | c | cat | d | dog |
| e | egg | f | fish | g | gun | h | hat |
| i | ink | j | jam | k | kite | l | lion |
| m | moon | n | nose | o | orange | p | pen |
| q | queen | r | rabbit | s | snake | t | tiger |
| u | umbrella | v | violin | w | whale | x | x-ray |
| y | yoyo | z | zebra | | | | |

- 每按一個鍵就一個圖像，依序串起來：各 = `rabbit kite rabbit = R+K+R`。
- 大寫圖像代表按住 Shift：애 = `dog orange`（d,o）、얘 = `dog ORANGE`（d,O）。
- 單字母列只有一個圖像：ㄱ = `rabbit = R`。
- 三個例外沿用使用者已看過的英文單字：아 `duke`、가 `ark`、강 `arked`。
- **L0 列刻意留空**（字母層不拿來測試）。

### 5.7 音檔（測驗時播放發音）

- 數量：**809 段**＝793 音節 ＋ 13 子音字母名 ＋ 3 母音音值；L0 不做音檔。
- 唸法：音節唸該字（가）；子音唸字母名（ㄱ→기역、ㄲ→쌍기역…）；母音唸承載它的音節（ㅏ→아）。
- 引擎：edge-tts `ko-KR-HyunsuMultilingualNeural`（男聲），輸出 `audio/syl|jamo/<碼點>.mp3`，去靜音＋−16 LUFS 正規化，單聲道 24 kHz 48 kbps，0.3–0.6 秒、2–3 KB。
- **授權**：edge-tts 是逆向使用 Edge 朗讀服務，輸出沒有明文授權（Apple `say` 更明文禁止 recording／redistribution）。使用者 2026-11-26 決定**接受殘餘風險、音檔照樣進 repo**，若日後被要求下架即 `rm -rf audio/` 一個 commit 收掉，頁面自動變無聲版。
- repo 內容：`audio/`（3.2 MB 音檔）＋ `code/make_audio.py` ＋ `data/audio-manifest.json`（char／spoken／duration／sha256）。
- 換引擎時整批重生成即可：改 `VOICE`，或把寫檔端換成本地引擎（MeloTTS KR 為 MIT 可散布，但單一聲音為女聲 172 Hz）。

## 6. Decisions Log

| # | Question | Decision |
|---|---|---|
| 1 | 鍵位欄代表什麼 | 實際按鍵序列；判定＝餵進鍵盤配置重算，輸出必須等於 B 欄（不多不少） |
| 2 | 大小寫規則 | 只有 Shift 層 7 鍵（Q W E R T O P）用大寫，其餘一律小寫 |
| 3 | ㅒ／ㅖ 寫法 | 單鍵 `O`／`P`；`Shift + o, i` 的 `, i` 是多餘的 ㅑ，刪除 |
| 4 | 兩種標記法並存 | rows 2–62 統一改為 rows 63+ 的緊湊式（`R`、`dhk`） |
| 5 | ㅎ 的鍵位 | `g`（`h` 是 ㅗ）；싫、잃 兩列因此修正 |
| 6 | 重複列 | L5 `구` 與 L3 重複 → 刪 L5 |
| 7 | 會單獨出現的字母 | 原 `0c` 的 13 個、`0v` 的 3 個改列 `L1c`／`L1v`，其餘留作字母表（後改名見 #15） |
| 8 | 過濾依據 | 語料（688k 詞形）∪ 詞典（134k 條目）；只用語料會誤刪 홰／몌／좨 |
| 9 | L4 處理 | 兩邊皆無者直接刪（41 列），不做標記保留 |
| 10 | L3 殘留 4 字 | 確認非常用 → 刪（꾜 뚀 뜌 뺘） |
| 11 | 詞典限定 6 字 | 5 個古語／方言刪除，홰 保留 |
| 12 | 目錄結構 | `code/` 放程式、`data/` 放資料與語料；腳本以 `../data/` 相對定位 |
| 13 | 定案後是否持續執行 | 不。字母與清單定案後程式不再自動跑，僅改表後手動驗證 |
| 14 | 驗證方式 | 每次改動後跑 `code/validate_krchar.py`，回報「PASS / 總列數」 |
| 15 | 分類前綴語意 | `0c/0v/0d` 改名 `L0c/L0v/L0d`（24 列）：前綴一律 `L`＋級別；`0` = 字母表（不單獨成字、只練鍵位），`1` 以上 = 可練打目標（2026-11-26） |
| 16 | memo 記憶法 | 26 個圖像詞（一鍵一詞）組成字串，大寫＝Shift，尾附 `= 鍵位`；L0 留空；아/가/강 保留英文單字 peg（2026-11-26） |
| 17 | 測驗發音 | edge-tts 男聲生成 809 段；子音唸字母名、母音唸音節（2026-11-26） |
| 21 | 換聲音 | InJoon 唸短母音（ㅠ）只有 0.12 秒有聲段，聽起來像被切斷 → 全部改用 `HyunsuMultilingualNeural` 重生成，尾端保留 120 ms（2026-11-27） |
| 22 | 答對提示音 | 答對時播 0.5 秒「叮」（`audio/ui/ding.mp3`），早於 2 秒跳題與下一題發音；答錯不播（只重播字音）（2026-11-28） |
| 23 | L1 專用聲音 | L1 26 張（13 子音名＋3 母音＋10 音節）改用 macOS `Yuna`（`code/make_audio_l1_yuna.py`），其餘 783 段維持 Hyunsu；`make_audio.py --force` 之後要補跑此腳本（2026-11-28） |
| 24 | Enter 換題 | 答案已揭露（錯 3 次或答對後 2 秒等待中）按 Enter 等同按 `Next`，不必用滑鼠；編輯對話框開啟時不攔截（2026-11-28） |
| 18 | 音檔是否進 repo | **進**：使用者接受 Edge TTS 授權的殘餘風險，公開站要能播放；被要求下架時 `rm -rf audio/` 一個 commit（頁面自動無聲），manifest 保留（2026-11-26） |
| 19 | 長期資料架構 | **Worker + D1**（同 `esflash-d1` 模式）；Google Sheet 只是初稿，定稿後整份複製進 D1 並停用 Sheet；因不再回寫 Sheet，**不需要 `sheet_pending` 與 `row_no`**（2026-11-26） |
| 20 | D1 內容切分 | `cards`＝共用內容（含 memo）；`card_stats`＝每人 weight／correct／wrong；`reviews`＝作答紀錄；主鍵用碼點 `cp`，排序用 `ord` 保留 L1→L6 進度（2026-11-26） |

## 7. Next Steps

- [x] 匯出 KRChar → `data/KRChar.csv` / `.json`
- [x] 鍵位稽核（883 列）並修正 9 格
- [x] 標記法統一（rows 2–62）
- [x] 刪重複列、L4／L3 不實用列、古語列（共 51）
- [x] 字母重新分類（L1c 13、L1v 3）
- [x] `code/`＋`data/` 分拆、驗證器改相對路徑、本地鏡像測試 PASS
- [x] README、本 plan 檔
- [x] 音檔：809 段（793 音節＋13 子音名＋3 母音值），edge-tts 男聲，本機生成
- [x] Worker API（health／cards／stats／review／card）＋ `X-Admin-Token` 保護
- [x] 測驗頁（level 累積、RR／Dubeolsik toggle、keydown 計分、3 次鎖卡公布答案、2 秒跳題、發音）
- [x] `/table` 瀏覽頁（833 筆、100 列／頁、搜尋／篩選／排序、就地編輯）
- [x] 本機驗證：smoke 17 條全過；瀏覽器實測（答對→2 秒跳題、三錯→公布＋鎖卡、RR 模式大小寫不敏感、音檔可播）
- [x] repo push（`github.com/fred09280928/krchar`, public）→ `wrangler secret put ADMIN_TOKEN` → `wrangler deploy` → 正式站 smoke 17/17 → 入口站 `apps.json` 已登錄
- [x] 專案上 GitHub（比照其他專案）→ 待 push
- [ ] 若日後改 Google Sheet：重新匯出並跑驗證（目前雲端與 `data/` 同步，833 列）
- [ ] （未定）是否把 `memo` 欄用於記錄個人常錯鍵位
- [ ] （未定）是否另做隨機順序的演練介面

---

## 8. D1（雲端資料庫，2026-11-26 建立）

Cloudflare D1 `krchar`（region APAC，帳號 `fred0928@gmail.com`）

- `database_id`：`550364a8-da18-43a9-9291-76107bbb1760`
- 表：`cards`（cp／hangul／category／rr／keys／memo／ord）、`card_stats`（owner／cp／weight／correct／wrong／last）、`reviews`、`meta`
- 灌入方式：

```bash
python3 code/export_seed.py                                   # CSV -> d1/seed.sql
npx wrangler d1 execute krchar --remote --file=d1/schema.sql
npx wrangler d1 execute krchar --remote --file=d1/seed.sql
```

- 驗證（實測）：**833 筆**、memo 已填 **809**、分類分佈與 CSV 完全相同、抽樣 ㄱ `r`／가 `rk`／몫 `ahrt` 與 memo 皆正確。
- 之後的資料修改以 D1 為準，repo 的 `seed.sql` 需反向匯出才會同步（`export_d1_seed.py` 尚未寫）。

## 9. 備註

- **最終數字（2026-11-26）**：833 列；字母 40（L1c 13、L1v 3、0c 6、0v 7、0d 11）、音節 793（L1 10、L2 11、L3 174、L4 155、L5 409、L6 34）；鍵位驗證 833 PASS / 0 mismatch；無重複；793 音節全部有出處。
- **執行限制**：本資料夾位於 iCloud Drive（`~/Library/Mobile Documents/com~apple~CloudDocs/…`），Hermes 的 lifecycle guard 拒絕執行雲端同步路徑下的腳本。要跑驗證請先複製到本機（例如 `~/Documents/myCode/KRChar`）。
- **同步方式**：Google Sheet 是 source of truth，`data/` 是快照；改了雲端要重新匯出，改了本機 CSV 不會回寫雲端。
- **未處理**：L5／L6 未逐字人工複核（只做過鍵位與出處檢查）；`memo` 全空。

建立日期：20261126
