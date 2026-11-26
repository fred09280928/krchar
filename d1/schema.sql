-- KRChar D1 schema (Cloudflare D1 / SQLite)
-- 內容（cards）與個人練習狀態（card_stats）分開；Sheet 定稿後不再參與，D1 是唯一來源。

CREATE TABLE IF NOT EXISTS cards (
  cp       TEXT    PRIMARY KEY,          -- 碼點，例如 'AC00'（가）；穩定、免 UUID
  hangul   TEXT    NOT NULL UNIQUE,      -- 字／字母本身
  category TEXT    NOT NULL,             -- L0c/L0v/L0d/L1c/L1v/L1..L6
  rr       TEXT    NOT NULL DEFAULT '',  -- Revised Romanization
  keys     TEXT    NOT NULL,             -- Dubeolsik 按鍵序列，例如 'rk'
  memo     TEXT    NOT NULL DEFAULT '',  -- 記憶提示（共用內容）
  ord      INTEGER NOT NULL UNIQUE       -- 原表順序，維持 L1→L6 練習進度
);

CREATE INDEX IF NOT EXISTS idx_cards_category ON cards(category);
CREATE INDEX IF NOT EXISTS idx_cards_ord      ON cards(ord);

-- 每人一份的權重與成績（cards.weight 不存這裡的狀態）
CREATE TABLE IF NOT EXISTS card_stats (
  owner   TEXT    NOT NULL DEFAULT 'fred0928',
  cp      TEXT    NOT NULL,
  weight  INTEGER NOT NULL DEFAULT 12 CHECK (weight BETWEEN 1 AND 15),
  correct INTEGER NOT NULL DEFAULT 0,
  wrong   INTEGER NOT NULL DEFAULT 0,
  last    TEXT,
  PRIMARY KEY (owner, cp)
);

CREATE INDEX IF NOT EXISTS idx_card_stats_owner ON card_stats(owner);

CREATE TABLE IF NOT EXISTS reviews (
  id     INTEGER PRIMARY KEY AUTOINCREMENT,
  ts     TEXT NOT NULL,                  -- 'YYYY-MM-DD HH:MM:SS'（Asia/Taipei，見 worker）
  owner  TEXT NOT NULL DEFAULT 'fred0928',
  cp     TEXT NOT NULL,
  action TEXT NOT NULL,                  -- review | edit | import
  result TEXT NOT NULL DEFAULT '',       -- correct | wrong | hint
  note   TEXT NOT NULL DEFAULT '',
  mode   TEXT NOT NULL DEFAULT ''        -- rr | dubeolsik（作答時的模式）
);

CREATE INDEX IF NOT EXISTS idx_reviews_cp        ON reviews(cp, ts);
CREATE INDEX IF NOT EXISTS idx_reviews_owner_ts  ON reviews(owner, ts);

CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT NOT NULL);
