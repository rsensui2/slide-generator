# Contributing to slide-generator

Thanks for your interest in contributing! slide-generator は実用のフィードバックで進化するプロジェクトです。

## 🎯 Contribution Areas

特に歓迎:

1. **新しい Provider 追加** — Stability AI, Midjourney API, Flux 等
2. **テンプレート追加** — `prompt_template_*.j2`（Visual/Balanced以外のスタイル）
3. **プリセット追加** — `references/presets/*.md`（業界別ブランドサンプル）
4. **日本語以外のローカライゼーション** — 英語・中国語プロンプトテンプレ
5. **バグ報告・改善提案**

## 📝 Issues

バグ報告の際は以下を含めてください:

```
**環境**
- OS: macOS 14.x
- Python: 3.11.x
- Provider: openai / gemini
- モデル: gpt-image-2 等

**再現手順**
1. ...
2. ...

**期待結果**
...

**実際の結果**
（エラーメッセージ・スクリーンショット）
```

## 🔀 Pull Requests

### 一般的なフロー

```bash
# 1. Fork → clone
git clone https://github.com/YOUR_USERNAME/slide-generator.git
cd slide-generator

# 2. ブランチ作成
git checkout -b feature/new-provider-stability

# 3. 実装
# ...

# 4. Commit
git commit -m "feat: add Stability AI provider"

# 5. Push & PR
git push origin feature/new-provider-stability
```

### Commit メッセージ規約

[Conventional Commits](https://www.conventionalcommits.org/) に準拠:

- `feat:` 新機能
- `fix:` バグ修正
- `docs:` ドキュメントのみ
- `refactor:` 機能変更なしのリファクタ
- `test:` テスト追加・修正
- `chore:` ビルド・補助ツール

### コードスタイル

- Python: [PEP 8](https://pep8.org/)（コメントは日本語 or 英語、内部統一されていればOK）
- Jinja2: インデント2スペース、コメント `{# ... #}` で意図を明示
- Markdown: ATX 見出し (`# h1`)、行末スペースなし

## 🧪 テスト

```bash
# 単体テスト
python3 -m pytest tests/

# 実生成テスト（API使用）
python3 scripts/compare_providers.py --limit 3 --prompts-dir ...
```

## 🎨 新しい Provider を追加する

### テンプレート

`scripts/providers/your_provider.py`:

```python
from .base import ImageProvider, ImageRequest, ImageResponse, Capability

class YourProvider(ImageProvider):
    CAPABILITIES = Capability(
        name="your_provider",
        model="your-model-v1",
        native_16_9=True,
        max_reference_images=10,
        supports_grounding=False,
        supports_thinking=False,
        supports_transparent_bg=False,
        default_parallel=10,
        size_map={
            "512px": "...",
            "1K":    "...",
            "2K":    "...",
            "4K":    "...",
        }
    )

    def generate(self, request: ImageRequest) -> ImageResponse:
        # 実装
        pass
```

`scripts/providers/registry.py` に登録:

```python
from .your_provider import YourProvider

_PROVIDERS["your_provider"] = YourProvider
```

## 🎭 新しいプリセットを追加する

`references/presets/industry-finance.md` のような形で:

```markdown
# [業界名] Preset

## Design Specifications

### 配色パレット
- Primary: #HEX
...

## レイアウトパターン
...
```

README またはテンプレート README にリンクを追加すると発見されやすい。

## 📋 PR チェックリスト

提出前に:

- [ ] コードが lint / format 通っている
- [ ] 該当する場合はテスト追加
- [ ] ドキュメント更新（README.md, docs/ など）
- [ ] API キーや個人情報が漏れていない
- [ ] 既存テストが通る
- [ ] コミットメッセージが Conventional Commits 準拠

## 🔐 セキュリティ

脆弱性を発見した場合:

- **公開 Issue に書かないでください**
- 代わりに rsensui@tekion.jp までメール

## 📜 ライセンス

このリポジトリへの貢献は MIT License のもとで公開されることに同意したものとみなされます。

## 💬 質問・議論

- **GitHub Discussions** で気軽に質問してください
- **X (Twitter)**: [@rsensui](https://x.com/rsensui)

---

Thanks for making slide-generator better! 🙏
