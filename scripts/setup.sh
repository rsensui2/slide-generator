#!/bin/bash
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo ""
echo "============================================"
echo "  nano-banana Slide Generator v3 Flash"
echo "  セットアップ"
echo "============================================"
echo ""

# --------------------------------------------------------
# 1. Python チェック
# --------------------------------------------------------
if ! command -v python3 &> /dev/null; then
    echo "❌ python3 が見つかりません。"
    echo ""
    echo "   Python 3.10 以上をインストールしてください:"
    echo "     Mac:   brew install python3"
    echo "     Ubuntu: sudo apt install python3 python3-pip"
    echo "     Windows: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✓ Python ${PYTHON_VERSION} を検出しました"

# --------------------------------------------------------
# 2. 依存パッケージの自動インストール
# --------------------------------------------------------
MISSING=()
python3 -c "import PIL" 2>/dev/null || MISSING+=("Pillow>=10.0.0")
python3 -c "import pptx" 2>/dev/null || MISSING+=("python-pptx>=0.6.21")
python3 -c "import requests" 2>/dev/null || MISSING+=("requests>=2.31.0")
python3 -c "import jinja2" 2>/dev/null || MISSING+=("Jinja2>=3.1.0")

if [ ${#MISSING[@]} -gt 0 ]; then
    echo ""
    echo "📦 不足パッケージをインストールします: ${MISSING[*]}"
    pip3 install "${MISSING[@]}" -q 2>/dev/null || python3 -m pip install "${MISSING[@]}" -q
    echo "✓ インストール完了"
else
    echo "✓ 必要なパッケージはすべてインストール済みです"
fi

# 最終確認
if ! python3 -c "import PIL, pptx, requests, jinja2" 2>/dev/null; then
    echo ""
    echo "❌ パッケージのインストールに失敗しました。"
    echo "   手動でインストールしてください:"
    echo ""
    echo "   pip3 install Pillow python-pptx requests Jinja2"
    echo ""
    exit 1
fi

echo "✓ 全パッケージの動作確認 OK"

# --------------------------------------------------------
# 3. SubAgent のインストール（ルートB使用時に必要）
# --------------------------------------------------------
AGENT_SRC="${SKILL_DIR}/agents/nanobanana-prompt-generator-subagent.md"
AGENT_DST_DIR="${HOME}/.claude/agents"
AGENT_DST="${AGENT_DST_DIR}/nanobanana-prompt-generator-subagent.md"

if [ -f "${AGENT_SRC}" ]; then
    mkdir -p "${AGENT_DST_DIR}"
    if [ ! -f "${AGENT_DST}" ]; then
        cp "${AGENT_SRC}" "${AGENT_DST}"
        echo "✓ SubAgent をインストールしました (${AGENT_DST})"
    else
        echo "✓ SubAgent は既にインストール済みです"
    fi
fi

# --------------------------------------------------------
# 4. Gemini API キーの確認
# --------------------------------------------------------
echo ""

# .env.local から読み込み
API_KEY_FOUND=false
for ENV_FILE in ".env.local" "${HOME}/.claude/.env.local"; do
    if [ -f "${ENV_FILE}" ] && grep -q "GEMINI_API_KEY" "${ENV_FILE}" 2>/dev/null; then
        API_KEY_FOUND=true
        echo "✓ APIキーを確認しました (${ENV_FILE})"
        break
    fi
done

if [ "${API_KEY_FOUND}" = false ] && [ -z "${GEMINI_API_KEY:-}" ]; then
    echo "⚠️  Gemini APIキーが設定されていません。"
    echo ""
    echo "   スライドを生成するにはAPIキーが必要です。"
    echo "   以下の手順で設定してください:"
    echo ""
    echo "   1. https://aistudio.google.com/apikey を開く"
    echo "   2. 「APIキーを作成」をクリック"
    echo "   3. 以下のコマンドを実行:"
    echo ""
    echo "      echo \"GEMINI_API_KEY=ここにコピーしたキーを貼り付け\" > ~/.claude/.env.local"
    echo ""
else
    if [ -n "${GEMINI_API_KEY:-}" ]; then
        echo "✓ APIキーを確認しました (環境変数)"
    fi
fi

# --------------------------------------------------------
# 完了
# --------------------------------------------------------
echo ""
echo "============================================"
echo "  ✓ セットアップ完了！"
echo "============================================"
echo ""
echo "  使い方:"
echo "    Claude Code で「スライドを作って」と"
echo "    話しかけるだけで自動的に起動します。"
echo ""
