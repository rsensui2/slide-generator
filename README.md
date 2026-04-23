# 🎨 slide-generator v4 — Release Notes

**AI駆動のプレゼンスライド自動生成ツール**
Markdown を書くだけで、OpenAI GPT-image-2 / Gemini 3.1 Flash が高品質な 16:9 2K スライドを並列生成。
PPTX / PDF まで一気通貫で出力。

---

## ⚡ TL;DR

**v4 で、スライド生成ツールが完成形に到達。**

- **OpenAI GPT-image-2 デフォルト対応**（日本語テキスト精度が圧倒的）
- **Visual / Balanced の2スタイル**（ピッチデッキ風 ↔ 営業資料風をフラグで切替）
- **スライド毎に個別スタイル指定可**（混在OK）
- **ロゴ色保全**（ピクセル忠実度の徹底）
- **Gemini も引き続き併用可**（大量生成・無料枠・実在ブランド描画はGemini）

---

## 🗺️ v1 → v4 進化の歩み

| バージョン | 時期 | コアテーマ | 到達点 |
|:---:|:---:|------|------|
| **v1** | 2026-01 | 原型 | Markdown → スライド画像 → PPTX の基本パイプライン確立 |
| **v2** | 2026-02 | ブランド対応 | デザインガイドライン概念導入、プロジェクト固有カラー・トーン反映可能に |
| **v3-flash** | 2026-03 | 高品質・高速 | Gemini 3.1 Flash Image、Thinking制御、グラウンディング、16:9 2K |
| **v4** | 2026-04 | マルチプロバイダ・スタイル制御 | OpenAI両対応、Visual/Balanced、配布可能品質 |

### v1 → v4 の**一番の進化**

> **「Markdown を投げ込めば、プレゼン業界のトップランナーがデザインしたような資料が出てくる」**
> という体験が **現実になったこと**。
> v1 は「動くだけ」、v4 は「使える」「配れる」「通用する」レベル。

具体的には:
- **解像度**: 1K → **2K (2752×1536) ネイティブ16:9**
- **日本語精度**: 崩れる → **誤字・切れなしの完璧レベル**
- **配布可否**: 試作品 → **クライアント提案書として使える品質**
- **生成速度**: 1枚ずつ → **15-16枚を5-7分で並列**
- **制御性**: デフォルト一択 → **スタイル・プロバイダ・解像度・品質を柔軟に切替**

---

## 🎯 v3-flash → v4 アップデート詳細

### 1. OpenAI GPT-image-2 対応（Provider 抽象レイヤ）

**Before (v3-flash)**: Gemini 3.1 Flash Image only
**After (v4)**: OpenAI GPT-image-2 / Gemini 3.1 Flash の両対応（**デフォルト: OpenAI**）

```bash
# デフォルト（OpenAI）
python3 generate_slides_parallel.py --prompts-dir ... --output-dir ...

# Gemini に切替
python3 generate_slides_parallel.py --provider gemini ...
```

**内部アーキテクチャ**:
- `providers/base.py` — 抽象基底クラス (`ImageProvider`, `ImageRequest`, `ImageResponse`, `Capability`)
- `providers/openai.py` — gpt-image-2 実装（`/images/generations` + `/images/edits`）
- `providers/registry.py` — プロバイダ解決

### 2. 🎨 Visual / Balanced の 2 スタイル

**Before (v3-flash)**: 情報密度高めの1スタイル固定
**After (v4)**: 用途別に2スタイル + スライド個別オーバーライド

| スタイル | 想定用途 | 文字量 | ビジュアル比率 |
|:---:|------|:---:|:---:|
| **Balanced**（デフォルト） | 営業資料・提案書 | 見出し+3-5項目 | 40-60% |
| **Visual** | 登壇・ピッチ・中扉 | タイトル+1-2行 | **60-80%** |

```bash
# セッション全体を Visual に
python3 generate_prompts_from_json.py ... --style visual

# JSON でスライド毎に指定（混在OK）
{"source_file": "00_cover", "_style": "visual", ...}
{"source_file": "01_body", ...}  ← --style デフォルト継承
```

### 3. 🖼️ ロゴ色保全の徹底

**Before**: ロゴが AI により再描画され、色反転や色変化が発生
**After**: 「添付画像をそのまま貼り付けるイメージで配置」という **ポジティブ指示** + 配置エリア清浄化ルール

テンプレート内の `logo:` セクション:
```yaml
instruction: "添付されたロゴ画像を、ピクセル単位で忠実に、そのまま配置すること"
clean_area: "ロゴを配置するエリアは白または極薄無地の背景にし、装飾を重ねない"
as_is: "ロゴの色・形・文字の書体・太さ・比率は、提供画像と完全に同じ"
```

### 4. 🖥️ 16:9 真・ネイティブ対応

**Before (v3-flash)**: Gemini のみ 16:9 ネイティブ、OpenAI は非対応と誤認
**After (v4)**: **両プロバイダで 2752×1536 完全一致**

OpenAI 側の制約を精査し、以下を確認:
- 両辺 16px の倍数必須（1920×1080 は非対応、1792×1008 / 2752×1536 / 3840×2160 はOK）
- 総ピクセル 655,360〜8,294,400
- 長辺:短辺 3:1 以内

| ラベル | Gemini | OpenAI |
|:---:|:---:|:---:|
| 512px | 960×540 | 1280×720 |
| 1K | 1920×1080 | 1792×1008 |
| **2K** | **2752×1536** | **2752×1536** |
| 4K | 3840×2160 | 3840×2160 |

### 5. 📦 参考画像マップの対応強化

**Before (v3-flash)**: Gemini `inlineData` で1枚
**After (v4)**: OpenAI `/images/edits` で **最大16枚**の参考画像（ロゴ + 人物 + 商品 + ブランドビジュアル）同時渡し可

```json
{
  "Ryoko": "/path/to/ryoko_avatar.jpeg",
  "5-1.1_オープニング_07": "/path/to/specific_image.png"
}
```
キーがスライド名に**部分一致**すれば自動適用。

### 6. 🛠️ 比較ツール `compare_providers.py` 新設

同じプロンプトで Gemini / OpenAI 両方を並列生成し、比較レポート（Markdown + JSON）を出力:

```bash
python3 compare_providers.py --prompts-dir ... --output-dir ${SESSION}/compare
```

出力:
```
compare/
├── comparison.md     # 成功率・平均時間・エラーサマリー
├── comparison.json   # 後続集計用データ
├── gemini/*.png
└── openai/*.png
```

### 7. 📝 ドキュメント強化

- [docs/style-prompt-diff.md](docs/style-prompt-diff.md) — Visual vs Balanced 差分解説 + 「デザインが今ひとつ問題」分析
- SKILL.md にスタイル選択・Provider 選択セクション刷新
- README.md 更新

---

## 🎁 v4 のフル機能リスト

### Provider
- ✅ **OpenAI GPT-image-2**（デフォルト、2K/3:2・16:9対応、最大16枚参考画像）
- ✅ **Google Gemini 3.1 Flash Image Preview**（Thinking / Grounding）
- ✅ Provider抽象レイヤ（新プロバイダ追加が容易）

### 制御
- ✅ `--style {visual|balanced}` + `_style` 個別オーバーライド
- ✅ `--image-size {512px|1K|2K|4K}` 両プロバイダ統一ラベル
- ✅ `--quality {auto|low|medium|high}` (OpenAI)
- ✅ `--thinking-level {minimal|High}` (Gemini)
- ✅ `--grounding-map` スライドごとの Google 画像検索ON/OFF (Gemini)
- ✅ `--background {auto|transparent|opaque}` (OpenAI)
- ✅ `--input-fidelity {low|high}` 参考画像忠実度 (OpenAI - gpt-image-1.5)

### リソース
- ✅ `--logo` 全スライド共通ロゴ（自動配置 + 色保全）
- ✅ `--reference-image-map` スライドごとの参考画像
- ✅ `design_guidelines.md` プロジェクト固有ブランド定義
- ✅ プリセット（カスタマイズ可）

### 出力
- ✅ PPTX (python-pptx, 2K埋め込み)
- ✅ PDF (Pillow, 2K埋め込み)
- ✅ PNG 個別画像

### ワークフロー
- ✅ Markdown → SubAgent並列分析 → JSON → プロンプト生成 → 並列画像生成 → PPTX/PDF
- ✅ 単一スライド再生成（バージョニング `_v2.png` `_v3.png`）
- ✅ プロンプト検証（render_test.py）

---

## 🚀 クイックスタート

```bash
# 1. API キー設定
echo "OPENAI_API_KEY=sk-..." >> ~/.claude/.env.local
echo "GEMINI_API_KEY=AIza..." >> ~/.claude/.env.local   # optional

# 2. 依存インストール
pip install Pillow python-pptx requests Jinja2

# 3. スキル起動（Claude Code）
「スライドを作って」
# → Markdown指定 → スタイル選択 → 自動生成
```

### 典型的なコマンド（手動）

```bash
SESSION=~/Desktop/slides_output/my_project
mkdir -p ${SESSION}/{json,prompts,images}
cp path/to/preset.md ${SESSION}/design_guidelines.md
# slides_plan.json を手動 or SubAgent で作成
# ...
python3 generate_prompts_from_json.py --session-dir ${SESSION} --style balanced
python3 generate_slides_parallel.py --prompts-dir ${SESSION}/prompts --output-dir ${SESSION}/images --api-key "${OPENAI_API_KEY}" --max-parallel 10 --quality high --logo ./assets/logo.png
python3 export_to_pptx.py --input-dir ${SESSION}/images --output ~/Desktop/output.pptx
```

---

## 💡 Before / After サンプル

### 営業資料（Balanced スタイル）
- 情報網羅・図解カード・箇条書きをバランスよく
- 配布用途に最適（提案書・ピッチ・法人営業）

### 登壇資料（Visual スタイル）
- タイトル + 1文のみ、ビジュアルが主役
- ステージ・TED・Keynote 風のインパクト重視

---

## 🏆 v4 を他ツールと比較すると

| 軸 | Canva / Gamma | Google Slides + AI | **slide-generator v4** |
|:---:|:---:|:---:|:---:|
| Markdown → 完成PPT | ❌（GUI操作必要） | 部分的 | ✅（完全自動） |
| 日本語フォント | 一部崩れ | 崩れる | ✅ **ピクセル単位の精度** |
| ブランド一貫性 | 手動テンプレ | 手動 | ✅ design_guidelines で一元管理 |
| カスタム制御 | GUI限定 | 限定 | ✅ プロンプトレベルで完全制御 |
| 16:9 2K ネイティブ | ✅ | ✅ | ✅ |
| API 自動化 | ❌ | 限定 | ✅ |
| コスト | $10-20/月 | $12/月 | 従量 ($2-4 / 16枚) |

---

## 📜 ライセンス

MIT（予定）

## 🤝 コントリビュート

Issues / Pull Requests 歓迎。

## 🔗 関連リソース

- [Gemini API 画像生成ドキュメント](https://ai.google.dev/gemini-api/docs/image-generation)
- [OpenAI Images API](https://developers.openai.com/api/reference/resources/images)
- [Claude Code Skills](https://docs.claude.com/en/docs/agents/skills)
