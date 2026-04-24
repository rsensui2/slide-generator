# 📦 Installation Guide

slide-generator の完全インストール手順。所要時間 5-10分。

---

## 前提条件

| 要件 | バージョン | 備考 |
|------|-----------|------|
| macOS / Linux | — | Windows は WSL2 推奨 |
| Python | 3.10+ | `python3 --version` で確認 |
| pip | 最新 | `pip install -U pip` |
| Claude Code | v2.x 以降 | [公式](https://claude.com/claude-code) |
| Git | 任意バージョン | clone 用 |

---

## 1. リポジトリ取得

```bash
git clone https://github.com/rsensui2/slide-generator.git
cd slide-generator
```

---

## 2. Claude Code Skill としてインストール

### オプション A: ディレクトリ配置（推奨・開発しやすい）

```bash
# スキルディレクトリに丸ごとコピー
cp -R . ~/.claude/skills/slide-generator/

# 再起動後、Claude Code で自動認識
```

### オプション B: `.skill` パッケージ（配布用）

将来 GitHub Release で `.skill` ファイルを配布予定。現状は自前ビルド:

```bash
python3 /path/to/skill-creator/scripts/package_skill.py . ~/.claude/skills/
```

→ `~/.claude/skills/slide-generator.skill` が生成される。

### オプション C: シンボリックリンク（更新が常に反映される）

```bash
ln -s $(pwd) ~/.claude/skills/slide-generator
```

git pull するだけで最新版が反映される。開発者向け。

---

## 3. Python 依存のインストール

```bash
pip install -r requirements.txt
```

内訳:
- `Pillow>=10.0.0` — 画像処理・PDF生成
- `python-pptx>=0.6.21` — PPTX 出力
- `requests>=2.31.0` — HTTP通信
- `Jinja2>=3.1.0` — プロンプトテンプレート

### 仮想環境（推奨）

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 4. API キーの設定

### OpenAI（推奨）

1. https://platform.openai.com/api-keys で API Key を作成
2. `~/.claude/.env.local` に追記:

```bash
echo 'OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx' >> ~/.claude/.env.local
chmod 600 ~/.claude/.env.local
```

### Gemini（オプション・大量生成用）

1. https://aistudio.google.com/apikey で API Key を作成
2. `~/.claude/.env.local` に追記:

```bash
echo 'GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXX' >> ~/.claude/.env.local
```

### 動作確認

```bash
source ~/.claude/.env.local
python3 -c "
import os, requests
r = requests.post(
    'https://api.openai.com/v1/images/generations',
    headers={'Authorization': f'Bearer {os.environ[\"OPENAI_API_KEY\"]}'},
    json={'model':'gpt-image-2','prompt':'test','size':'1024x1024','quality':'low','n':1,'output_format':'png'},
    timeout=60,
)
print('OpenAI:', r.status_code)
"
```

200 なら成功。

---

## 5. Claude Code 起動

### 推奨: Bypass Permissions モード

```bash
claude --dangerously-skip-permissions
```

または `~/.claude/settings.json` に:

```json
{
  "permissionMode": "bypassPermissions"
}
```

### 初回起動時の確認

Claude Code を起動して以下を確認:

```
/skills
```

`slide-generator` が表示されれば成功。

---

## 6. 動作テスト

### 簡単なスライド1枚生成

```bash
# 作業ディレクトリ
TEST=~/Desktop/slide-test
mkdir -p ${TEST}/{prompts,images}

# プロンプト作成
cat > ${TEST}/prompts/test_01.txt <<'EOF'
A clean presentation slide with title "テスト成功"
in the center, minimal design, white background with blue accent.
※スライド上の全テキストは日本語で表示すること。
EOF

# 画像生成
source ~/.claude/.env.local
python3 ~/.claude/skills/slide-generator/scripts/generate_slide_with_retry.py \
  --provider openai \
  --prompt "$(cat ${TEST}/prompts/test_01.txt)" \
  --output ${TEST}/images/test_01.png \
  --api-key "${OPENAI_API_KEY}" \
  --image-size 1K \
  --quality low
```

`${TEST}/images/test_01.png` が生成されれば完了。

---

## トラブルシューティング

### `ModuleNotFoundError: No module named 'PIL'`

```bash
pip install Pillow python-pptx requests Jinja2
```

### OpenAI 500 エラー

gpt-image-2 は新モデルでサーバー側の一時障害が起きることがある。
- 数分待つ
- `--provider gemini` でフォールバック
- 別モデルで切り分け: `--model gpt-image-1`（未実装。希望があればPR）

### Gemini 429（レート制限）

- 無料枠の上限に達している
- 並列数を下げる: `--max-parallel 5`

### 日本語が化ける

- 生成された PNG は UTF-8 ベース、問題なし
- PPTX/PDF で化ける場合は Adobe Reader / PowerPoint 最新版推奨

---

## アンインストール

```bash
rm -rf ~/.claude/skills/slide-generator
rm -f ~/.claude/skills/slide-generator.skill
# APIキーは残しておいて問題なし（他のスキル/ツールで使う場合）
```
