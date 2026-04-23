---
name: nanobanana-slide-generator-v4
description: "プレゼンスライド生成（OpenAI GPT-image-2 デフォルト / Gemini 3.1 Flash 両対応）。「スライドを作って」「プレゼン資料」で発動。Markdown/テキスト→デザインガイドライン→並列画像生成→PPTX/PDF。日本語テキスト精度重視の営業資料・提案書はOpenAI、大量生成や実在ブランド/人物はGemini。Visual/Balanced 2スタイル、ロゴ/参考画像、グラウンディング、Thinking制御対応。"
---

# nano-banana Slide Generator v4

## 実行モード

```yaml
mode: auto  # Pre-flight〜Phase 5を承認なしで連続実行
pause_only_on: [route_ambiguous, api_key_missing]
chain_commands: true  # bashは && で連結
```

## 定数

```bash
SKILL_DIR="<path-to-this-skill>"
PYTHON="python3"
```

## 前提条件

- Python 3.10+
- **Gemini API Key**（`.env.local` または `GEMINI_API_KEY` 環境変数） — `--provider gemini` 時
- **OpenAI API Key**（`.env.local` または `OPENAI_API_KEY` 環境変数） — `--provider openai` 時
- SubAgent定義（ルートB使用時）: `~/.claude/agents/nanobanana-prompt-generator-subagent.md`（`setup.sh` が `${SKILL_DIR}/agents/` から自動インストール）

初回セットアップ:
```bash
bash ${SKILL_DIR}/scripts/setup.sh
```

## 言語ルール

```yaml
display_language: "ターゲット聴衆に合わせる（素材の言語ではない）"
target_fields: [title, subtitle, key_message, content]
english_allowed: "固有名詞のみ (Cursor, MCP等)"
content_suffix: "※スライド上の全テキストは{lang}で表示すること。"
```

## スタイル選択

Phase 3 のプロンプト生成で `--style` フラグを指定、またはスライド毎に JSON で `_style` を付与することで、
スライドの雰囲気（文字量・ビジュアル比率・余白）を切り替えられます。

| 判断基準 | スタイル | テンプレート |
|----------|:---:|---|
| 「登壇」「ピッチ」「Keynote風」「ビジュアル重視」「写真主役」 | **visual** | `prompt_template_visual.j2` |
| 「営業資料」「提案書」「バランス」「図解と文字の両立」（デフォルト） | **balanced** | `prompt_template_balanced.j2` |

### visual スタイル（ピッチデッキ風）
- Apple Keynote / TED Talk の余白美学、Less is more
- タイトル15文字 + キーメッセージ1文（最大2行）
- 画面の**60-80%**を1つの大胆なビジュアル（全面写真・巨大数字・大きなシンボル）
- 複数カード・網羅リストは禁止、大胆な余白
- **用途**: 登壇・ピッチ・表紙・中扉・感情に訴える1枚

### balanced スタイル（営業資料・提案書風／デフォルト）
- Pitch.com / MorningBrew / Figma Slides の洗練
- 見出し + 3-5項目の簡潔な箇条書き / 2-3ブロックの図解
- テキスト40-60% / ビジュアル40-60%のバランス
- 情報網羅は求めず、要点を絞る
- **用途**: 営業資料・提案書・プラン比較・実績紹介（今回のVibeCoder Bootcamp資料相当）

### スライド毎のオーバーライド（`_style`）

`slides_plan.json` で個別指定可能:

```json
{
  "source_file": "00_cover",
  "_style": "visual",    ← 表紙だけ visual にする
  "title": "...",
  "content": "..."
}
```

`_style` が未指定なら `--style` のデフォルトを継承。

### ユースケース別レコメンド

| 用途 | 推奨 | 備考 |
|------|:---:|------|
| 登壇用ピッチ資料 | visual | 表紙・章扉・キーメッセージを visual で |
| 営業資料・提案書 | balanced | 今回の VibeCoder Bootcamp 相当 |
| 表紙＋本編の混在 | `--style balanced` + 表紙だけ `_style: visual` | 最も良く使うパターン |

## ルート選択

| 判断基準 | ルート |
|----------|--------|
| 「サクッと」「一括で」「まとめてスライドにして」 | B（高速） |
| 「いい感じに」「ちゃんと」「プレゼン用に」 | A（高品質） |
| 迷ったら聞く: 「丁寧に作る？サクッと作る？」 | — |

- **ルートA**: 10-15枚、見た目重視。JSON手動作成5-10分 + 生成2-3分
- **ルートB**: 20枚以上、速度重視。SubAgent並列JSON自動生成、全自動2-3分

## Provider選択

**デフォルトは OpenAI (gpt-image-2)**。特段の理由がない限り OpenAI を使う。

| 判断基準 | Provider |
|----------|:---:|
| 指定なし（デフォルト） | **openai** |
| 「OpenAIで」「GPTで」「gpt-image-2で」 | **openai** |
| 「Geminiで」「nano bananaで」「3.1 Flashで」 | **gemini** |
| 日本語テキスト精度・営業資料・提案書 | **openai** |
| Google検索グラウンディング必要 | **gemini** |
| 20枚以上の大量生成でコスト抑えたい | **gemini**（並列度20・無料枠） |
| 透明背景 / 参考画像多数（最大16枚） | **openai** |

**比較したい場合**: `compare_providers.py` で同じプロンプトで両方生成（後述）。

### レート制限の目安（OpenAI）

| Tier | IPM | 推奨`--max-parallel` |
|:---:|:---:|:---:|
| 1 | 5 | 3 |
| 2 | 20 | 8 |
| 3 | 50 | 10 |
| 4 | 150 | 20 |
| 5 | 250 | 20+ |

---

## Pre-flight

1. `.env.local` から `GEMINI_API_KEY` を確認（プロジェクトルート → `~/.claude/.env.local` の順）
2. 未設定 → **STOP**（APIキー取得案内: https://aistudio.google.com/apikey）
3. 依存チェック:

```bash
python3 -c "import PIL, pptx, requests, jinja2; print('OK')" 2>/dev/null || bash ${SKILL_DIR}/scripts/setup.sh
```

## Phase 0: セッション準備

```bash
TIMESTAMP=$(date +%Y-%m-%d_%H%M) && OUTPUT_DIR="[指定された出力先]" && SESSION_DIR="${OUTPUT_DIR}/slides_output/${TIMESTAMP}" && mkdir -p ${SESSION_DIR}/{json,prompts,images}
```

## Phase 1: デザインガイドライン作成

テンプレート: `${SKILL_DIR}/references/design_guidelines_template.md`

**プリセット使用時:**
```bash
cp ${SKILL_DIR}/references/presets/example-preset.md ${SESSION_DIR}/design_guidelines.md
```

**カスタム作成時** — テンプレート参照し以下を決定:
1. カラーパレット（テーマに合った色）
2. 写真スタイル（ターゲット層の年代・性別・シーン）
3. トーン（1-2文で方向性）
4. フォントサイズ（ターゲットに応じて調整）

```bash
cat > ${SESSION_DIR}/design_guidelines.md << 'EOF'
[カスタマイズした内容]
EOF
```

## Phase 2: slides_plan.json 作成（最重要）

### route_a: 手動作成

入力を読み、各スライドの content を丁寧に書く。

**content に含める項目:**
- `<!-- Pattern X: 説明 -->` — レイアウトヒント
- 表示テキスト全文（タイトル、箇条書き、数値データ）
- 背景写真指示（被写体、構図、雰囲気）
- 図解・アイコン・グラフの内容
- カラー使い分け（アクセント色の配置）
- 言語強制: `※スライド上の全テキストは{lang}で表示すること。`

**構成目安:** 表紙(G) → 課題提起(C/D) → ソリューション(B/C) → 市場(J) → ビジネスモデル(E) → 差別化(H/A) → ロードマップ(I) → まとめ(D) → CTA(G)

### route_b: SubAgent並列

1. MDファイルを Glob で検出
2. 3-5個ずつチャンク分割
3. 各チャンクに `nanobanana-prompt-generator-subagent` を並列起動（同一メッセージ内で複数Task呼び出し）
4. 統合:

```bash
${PYTHON} ${SKILL_DIR}/scripts/merge_chunks.py \
  --input-dir ${SESSION_DIR}/json \
  --output ${SESSION_DIR}/json/slides_plan.json
```

### グラウンディング制御

| `_grounding` | 条件 |
|:---:|------|
| `true` | 実在する製品・都市・ブランド・市場データ |
| `false`（デフォルト） | 抽象図解・テキスト中心・表紙/中扉・オリジナルイラスト |

### JSONスキーマ

```json
{
  "slides": [
    {
      "slide_number": 0,
      "source_file": "00_cover",
      "title": "タイトル",
      "subtitle": "サブタイトル",
      "content": "<!-- Pattern G --> ...",
      "key_message": "核心メッセージ1文",
      "_grounding": false
    }
  ],
  "total_slides": 12
}
```

**フィールド:**
- 必須: `slide_number`(数値), `source_file`(文字列), `title`, `subtitle`, `content`
- オプション: `key_message`(文字列), `_grounding`(真偽値)
- 禁止: `slide_type`, `layout`, `visual_description`（デザイン判断はGeminiが行う）

**命名規則:** 表紙 `"00_cover"` / 本編 `"01_xxx"`〜`"97_xxx"` / まとめ `"98_summary"` / CTA `"99_cta"`

### バリデーション

```bash
cat > ${SESSION_DIR}/json/slides_plan.json << 'JSONEOF'
{作成したJSON}
JSONEOF
${PYTHON} ${SKILL_DIR}/scripts/validate_slides_json.py --file ${SESSION_DIR}/json/slides_plan.json
```

## Phase 3: プロンプト生成 + グラウンディングマップ

```bash
${PYTHON} ${SKILL_DIR}/scripts/generate_prompts_from_json.py \
  --session-dir ${SESSION_DIR} \
  --json-file json/slides_plan.json \
  --output-dir prompts \
  --design-guidelines ${SESSION_DIR}/design_guidelines.md \
  --style balanced \
  --image-size 2K
```

**スタイル切替**:
- `--style balanced` (デフォルト) — 営業資料・提案書風
- `--style visual` — ピッチデッキ風（文字極少、ビジュアル主役）
- JSON で個別指定 — 各スライドに `"_style": "visual"` を書けば、そのスライドだけ Visual に

JSONでの混在例:
```json
{"source_file": "00_cover", "_style": "visual", "title": "...", "content": "..."},
{"source_file": "01_body", "title": "...", "content": "..."}
```
→ 表紙だけ Visual、本編は `--style` のデフォルト（balanced）を継承。

## Phase 3.5: プロンプト検証（任意）

```bash
${PYTHON} ${SKILL_DIR}/scripts/render_test.py \
  --session-dir ${SESSION_DIR} \
  --design-guidelines ${SESSION_DIR}/design_guidelines.md
```

## Phase 3.7: リファレンス画像マップ作成（任意）

特定のスライドに参照画像（キャラクター・ロゴ・写真等）をGeminiに渡したい場合、リファレンス画像マップを作成する。

```bash
cat > ${SESSION_DIR}/reference_image_map.json << 'JSONEOF'
{
  "Ryoko": "/path/to/ryoko_avatar.jpeg",
  "5-1.1_オープニング_07": "/path/to/specific_image.png"
}
JSONEOF
```

**マッチングルール:**
- キーがスライドのベース名に**部分一致**すれば適用される
- 例: `"Ryoko"` → `5-3.6_総合ケーススタディ_Ryoko_01.png` にマッチ
- 完全一致キーが優先される

ユーザーが画像を添付した場合、`${SESSION_DIR}/images/` にコピーしてマップに登録する。

## Phase 4: スライド画像生成

### OpenAI GPT-image-2（デフォルト）

```bash
if [ -f .env.local ]; then source .env.local; elif [ -f ~/.claude/.env.local ]; then source ~/.claude/.env.local; fi && \
${PYTHON} ${SKILL_DIR}/scripts/generate_slides_parallel.py \
  --prompts-dir ${SESSION_DIR}/prompts \
  --output-dir ${SESSION_DIR}/images \
  --api-key "${OPENAI_API_KEY}" \
  --max-parallel 10 --max-retries 3 \
  --image-size 2K \
  --quality high \
  --logo ${SKILL_DIR}/assets/logo.png \
  --reference-image-map ${SESSION_DIR}/reference_image_map.json
```

`--provider openai` は省略可能（デフォルト）。並列数はTier 3想定で10、Tier 5なら20+まで増やせます。

### Gemini（サブ・大量生成向け）

```bash
if [ -f .env.local ]; then source .env.local; elif [ -f ~/.claude/.env.local ]; then source ~/.claude/.env.local; fi && \
${PYTHON} ${SKILL_DIR}/scripts/generate_slides_parallel.py \
  --provider gemini \
  --prompts-dir ${SESSION_DIR}/prompts \
  --output-dir ${SESSION_DIR}/images \
  --api-key "${GEMINI_API_KEY}" \
  --max-parallel 20 --max-retries 3 \
  --image-size 2K \
  --thinking-level High \
  --grounding-map ${SESSION_DIR}/grounding_map.json \
  --logo ${SKILL_DIR}/assets/logo.png \
  --reference-image-map ${SESSION_DIR}/reference_image_map.json
```

**注意事項:**
- **`--logo` は常に付与する** — ユーザーが明示的に「ロゴ不要」と言った場合のみ省略
- OpenAI時はロゴ・参考画像があるスライドは自動で `/images/edits` にルーティング
- OpenAI時は `--thinking-level` / `--grounding-map` は無視される（警告表示）
- OpenAI時の解像度マップ: `1K=1792x1008`, `2K=2752x1536`, `4K=3840x2160`（すべて16:9）

| パラメータ | デフォルト | 選択肢 | 適用 |
|-----------|:---------:|--------|:---:|
| `--provider` | gemini | gemini, openai | 両方 |
| `--image-size` | 2K | 512px, 1K, 2K, 4K | 両方 |
| `--logo` | `${SKILL_DIR}/assets/logo.png` | 常に付与 | 両方 |
| `--reference-image-map` | なし | JSONファイルパス | 両方 |
| `--thinking-level` | High | minimal, High | Geminiのみ |
| `--grounding-map` | なし | JSONファイルパス | Geminiのみ |
| `--quality` | high | auto, low, medium, high | OpenAIのみ |
| `--background` | auto | auto, transparent, opaque | OpenAIのみ |

### プロバイダ比較（実測）

同じプロンプトで Gemini / OpenAI を並列生成し、比較レポートを出力:

```bash
${PYTHON} ${SKILL_DIR}/scripts/compare_providers.py \
  --prompts-dir ${SESSION_DIR}/prompts \
  --output-dir ${SESSION_DIR}/compare \
  --gemini-api-key "${GEMINI_API_KEY}" \
  --openai-api-key "${OPENAI_API_KEY}" \
  --image-size 2K \
  --limit 5 \
  --logo ${SKILL_DIR}/assets/logo.png
```

出力: `${SESSION_DIR}/compare/{gemini,openai}/*.png` と `comparison.md`, `comparison.json`

## Phase 4.5: 単一スライド再生成（任意）

```bash
${PYTHON} ${SKILL_DIR}/scripts/regenerate_slide.py \
  --slide {source_file} \
  --session-dir ${SESSION_DIR} \
  --api-key "${GEMINI_API_KEY}" \
  --max-retries 3 \
  --image-size 2K \
  --thinking-level High \
  --logo ${SKILL_DIR}/assets/logo.png
```

グラウンディング有効時は `--grounding` を追加。
バージョニング: `_01.png` → `_01_v2.png` → `_01_v3.png`（Phase 5は最新を自動選択）

## Phase 5: PPTX/PDF生成

```bash
${PYTHON} ${SKILL_DIR}/scripts/export_to_pptx.py \
  --input-dir ${SESSION_DIR}/images --output ${OUTPUT_DIR}/${OUTPUT_NAME}.pptx && \
${PYTHON} ${SKILL_DIR}/scripts/export_to_pdf.py \
  --input-dir ${SESSION_DIR}/images --output ${OUTPUT_DIR}/${OUTPUT_NAME}.pdf
```

---

## 参照ドキュメント

| ファイル | 内容 |
|----------|------|
| [references/architecture.md](references/architecture.md) | アーキテクチャ図 + API仕様 |
| [references/troubleshooting.md](references/troubleshooting.md) | トラブルシューティング |
| [references/quality-checklist.md](references/quality-checklist.md) | 品質チェックリスト |
| [references/design_guidelines_template.md](references/design_guidelines_template.md) | デザインガイドラインテンプレート |
| [references/presets/](references/presets/) | プリセット集 |
| [templates/prompt_template.j2](templates/prompt_template.j2) | Jinja2テンプレート |
