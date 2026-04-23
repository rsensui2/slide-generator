#!/usr/bin/env python3
"""
nano-banana Slide Generator v3 Flash - Feature Tests

v3 Flash の新機能を検証するテストスイート。
API呼び出しなしで構造的正確性を検証する。

テスト対象:
  1. 解像度マッピング（RESOLUTION_MAP）
  2. grounding_map.json 生成（extract_grounding_map / save_grounding_map）
  3. validate_slides_json.py の _grounding フィールド通過
  4. Jinja2テンプレートの解像度動的レンダリング
  5. build_payload のグラウンディング / Thinking パラメータ
  6. generate_slides_parallel.py の grounding_map 読み込み

Usage:
    cd ~/.claude/skills/nanobanana-slide-generator-v3-flash
    python tests/test_v3_flash_features.py
"""

import json
import os
import sys
import tempfile
import shutil

# テスト対象スクリプトのパスを設定
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(SKILL_DIR, "scripts")
TEMPLATES_DIR = os.path.join(SKILL_DIR, "templates")

sys.path.insert(0, SCRIPTS_DIR)


# ============================================================
# Test Fixtures
# ============================================================

SAMPLE_SLIDES_PLAN = {
    "slides": [
        {
            "slide_number": 0,
            "source_file": "00_cover",
            "title": "AI時代の富の移転",
            "subtitle": "2025年最新トレンド",
            "content": "<!-- Pattern G --> 講座タイトルスライド（表紙）\n※スライド上の全テキストは日本語で表示すること。",
            "key_message": "AIがもたらす新しい経済パラダイム",
            "_grounding": False
        },
        {
            "slide_number": 1,
            "source_file": "01_market",
            "title": "市場動向",
            "subtitle": "中扉スライド：タイトルとサブタイトルのみ表示",
            "content": "中扉スライド：タイトルとサブタイトルのみ表示\n※スライド上の全テキストは日本語で表示すること。",
            "_grounding": False
        },
        {
            "slide_number": 2,
            "source_file": "01_market",
            "title": "AI市場規模",
            "subtitle": "急成長する市場",
            "content": "<!-- Pattern J --> AI市場は2030年までに1.5兆ドルに到達\n- 年平均成長率: 37.3%\n- 主要プレイヤー: OpenAI, Google, Anthropic\n※スライド上の全テキストは日本語で表示すること。",
            "key_message": "AI市場は爆発的に成長中",
            "_grounding": True
        },
        {
            "slide_number": 3,
            "source_file": "02_solution",
            "title": "ソリューション",
            "subtitle": "中扉スライド：タイトルとサブタイトルのみ表示",
            "content": "中扉スライド：タイトルとサブタイトルのみ表示\n※スライド上の全テキストは日本語で表示すること。",
            "_grounding": False
        },
        {
            "slide_number": 4,
            "source_file": "02_solution",
            "title": "具体的アプローチ",
            "subtitle": "3つのステップ",
            "content": "<!-- Pattern B --> ステップ1: 現状分析\nステップ2: 戦略策定\nステップ3: 実行\n※スライド上の全テキストは日本語で表示すること。",
            "_grounding": True
        }
    ],
    "total_slides": 5
}


# ============================================================
# Test Utilities
# ============================================================

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def ok(self, name):
        self.passed += 1
        print(f"  PASS  {name}")

    def fail(self, name, detail=""):
        self.failed += 1
        msg = f"  FAIL  {name}"
        if detail:
            msg += f": {detail}"
        self.errors.append(msg)
        print(msg)

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"Test Summary: {self.passed}/{total} passed, {self.failed} failed")
        print(f"{'='*60}")
        if self.errors:
            print("\nFailed tests:")
            for e in self.errors:
                print(f"  {e}")
        return self.failed == 0


# ============================================================
# Test 1: Resolution Mapping
# ============================================================

def test_resolution_mapping(results):
    """RESOLUTION_MAP の正確性を検証"""
    print("\n--- Test 1: Resolution Mapping ---")

    from generate_prompts_from_json import RESOLUTION_MAP

    expected = {
        "512px": "912x512",
        "1K": "1376x768",
        "2K": "2752x1536",
        "4K": "4096x2304",
    }

    for key, expected_val in expected.items():
        if key not in RESOLUTION_MAP:
            results.fail(f"RESOLUTION_MAP['{key}'] missing")
        elif RESOLUTION_MAP[key] != expected_val:
            results.fail(f"RESOLUTION_MAP['{key}']", f"expected {expected_val}, got {RESOLUTION_MAP[key]}")
        else:
            results.ok(f"RESOLUTION_MAP['{key}'] = {expected_val}")

    # 4つの解像度がすべて存在することを確認
    if len(RESOLUTION_MAP) == len(expected):
        results.ok("RESOLUTION_MAP has exactly 4 entries")
    else:
        results.fail("RESOLUTION_MAP entry count", f"expected 4, got {len(RESOLUTION_MAP)}")


# ============================================================
# Test 2: Grounding Map Extraction
# ============================================================

def test_grounding_map_extraction(results):
    """extract_grounding_map の正確性を検証"""
    print("\n--- Test 2: Grounding Map Extraction ---")

    from generate_prompts_from_json import extract_grounding_map, extract_file_basename

    slides = SAMPLE_SLIDES_PLAN["slides"]

    # _file_slide_number をシミュレート（main()内と同じロジック）
    per_file_counters = {}
    for slide in slides:
        source_file = slide.get('source_file', '')
        if source_file not in per_file_counters:
            per_file_counters[source_file] = 0
        per_file_counters[source_file] += 1
        slide['_file_slide_number'] = per_file_counters[source_file]

    grounding_map = extract_grounding_map(slides)

    # 5スライド分のエントリがあること
    if len(grounding_map) == 5:
        results.ok(f"grounding_map has {len(grounding_map)} entries")
    else:
        results.fail(f"grounding_map entry count", f"expected 5, got {len(grounding_map)}")

    # 各スライドのグラウンディング設定を検証
    expected_map = {
        "00_cover_01": False,
        "01_market_01": False,
        "01_market_02": True,
        "02_solution_01": False,
        "02_solution_02": True,
    }

    for key, expected_val in expected_map.items():
        if key not in grounding_map:
            results.fail(f"grounding_map['{key}'] missing")
        elif grounding_map[key] != expected_val:
            results.fail(f"grounding_map['{key}']", f"expected {expected_val}, got {grounding_map[key]}")
        else:
            results.ok(f"grounding_map['{key}'] = {expected_val}")


# ============================================================
# Test 3: Grounding Map Save/Load
# ============================================================

def test_grounding_map_save_load(results):
    """save_grounding_map のファイル出力を検証"""
    print("\n--- Test 3: Grounding Map Save/Load ---")

    from generate_prompts_from_json import save_grounding_map

    tmpdir = tempfile.mkdtemp()
    try:
        test_map = {"slide_01": True, "slide_02": False, "slide_03": True}
        output_path = save_grounding_map(tmpdir, test_map)

        # ファイルが作成されたことを確認
        expected_path = os.path.join(tmpdir, "grounding_map.json")
        if os.path.exists(expected_path):
            results.ok("grounding_map.json file created")
        else:
            results.fail("grounding_map.json file creation")
            return

        # 内容が正しいことを確認
        with open(expected_path, 'r', encoding='utf-8') as f:
            loaded = json.load(f)

        if loaded == test_map:
            results.ok("grounding_map.json content matches")
        else:
            results.fail("grounding_map.json content", f"expected {test_map}, got {loaded}")

    finally:
        shutil.rmtree(tmpdir)


# ============================================================
# Test 4: validate_slides_json.py - _grounding field passthrough
# ============================================================

def test_validate_grounding_field(results):
    """validate_slides_json.py が _grounding フィールドを許可することを検証"""
    print("\n--- Test 4: Validate _grounding Field Passthrough ---")

    from validate_slides_json import validate_slide, validate_chunk

    # _grounding: true のスライド
    slide_with_grounding = {
        "slide_number": 2,
        "source_file": "01_market",
        "title": "AI市場規模",
        "subtitle": "急成長する市場",
        "content": "中扉スライド：タイトルとサブタイトルのみ表示",
        "_grounding": True
    }

    issues = validate_slide(slide_with_grounding, 0)
    grounding_issues = [i for i in issues if '_grounding' in i]
    if not grounding_issues:
        results.ok("_grounding=true passes validation")
    else:
        results.fail("_grounding=true validation", str(grounding_issues))

    # _grounding: false のスライド
    slide_without_grounding = {
        "slide_number": 0,
        "source_file": "00_cover",
        "title": "表紙",
        "subtitle": "サブタイトル",
        "content": "中扉スライド：タイトルとサブタイトルのみ表示",
        "_grounding": False
    }

    issues = validate_slide(slide_without_grounding, 0)
    grounding_issues = [i for i in issues if '_grounding' in i]
    if not grounding_issues:
        results.ok("_grounding=false passes validation")
    else:
        results.fail("_grounding=false validation", str(grounding_issues))

    # 禁止フィールドが検出されることも確認
    slide_with_forbidden = {
        "slide_number": 1,
        "source_file": "01_test",
        "title": "テスト",
        "subtitle": "テスト",
        "content": "中扉スライド：タイトルとサブタイトルのみ表示",
        "slide_type": "content",  # forbidden
    }

    issues = validate_slide(slide_with_forbidden, 0)
    forbidden_issues = [i for i in issues if "forbidden field 'slide_type'" in i]
    if forbidden_issues:
        results.ok("Forbidden field 'slide_type' detected correctly")
    else:
        results.fail("Forbidden field detection", "slide_type should be forbidden")


# ============================================================
# Test 5: Jinja2 Template Resolution Rendering
# ============================================================

def test_template_resolution_rendering(results):
    """Jinja2テンプレートが解像度を動的にレンダリングすることを検証"""
    print("\n--- Test 5: Jinja2 Template Resolution Rendering ---")

    try:
        from jinja2 import Environment, FileSystemLoader
    except ImportError:
        results.fail("Jinja2 import", "Jinja2 not installed")
        return

    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        trim_blocks=True,
        lstrip_blocks=True
    )
    template = env.get_template("prompt_template.j2")

    test_slide = {
        "title": "テストスライド",
        "subtitle": "テストサブタイトル",
        "content": "テスト内容",
        "key_message": "テストメッセージ",
    }

    # 2K解像度でレンダリング
    rendered_2k = template.render(
        slide=test_slide,
        design_guidelines="テストガイドライン",
        chapter_context=None,
        resolution="2752x1536"
    )
    if '2752x1536' in rendered_2k:
        results.ok("2K resolution (2752x1536) rendered in template")
    else:
        results.fail("2K resolution rendering", "2752x1536 not found in output")

    # 4K解像度でレンダリング
    rendered_4k = template.render(
        slide=test_slide,
        design_guidelines="テストガイドライン",
        chapter_context=None,
        resolution="4096x2304"
    )
    if '4096x2304' in rendered_4k:
        results.ok("4K resolution (4096x2304) rendered in template")
    else:
        results.fail("4K resolution rendering", "4096x2304 not found in output")

    # 解像度未指定時のデフォルト
    rendered_default = template.render(
        slide=test_slide,
        design_guidelines="テストガイドライン",
        chapter_context=None,
    )
    if '2752x1536' in rendered_default:
        results.ok("Default resolution (2752x1536) used when not specified")
    else:
        results.fail("Default resolution", "2752x1536 not found when resolution not provided")

    # 512px解像度でレンダリング
    rendered_512 = template.render(
        slide=test_slide,
        design_guidelines="テストガイドライン",
        chapter_context=None,
        resolution="912x512"
    )
    if '912x512' in rendered_512:
        results.ok("512px resolution (912x512) rendered in template")
    else:
        results.fail("512px resolution rendering", "912x512 not found in output")


# ============================================================
# Test 6: build_payload with Grounding and Thinking
# ============================================================

def test_build_payload(results):
    """build_payload がグラウンディングとThinkingパラメータを正しく構築することを検証"""
    print("\n--- Test 6: build_payload Parameters ---")

    from generate_slide_with_retry import build_payload

    # グラウンディングなし
    payload_no_grounding = build_payload(
        prompt="テストプロンプト",
        image_size="2K",
        thinking_level="High",
        grounding=False,
    )

    # tools が存在しないこと
    if "tools" not in payload_no_grounding:
        results.ok("No 'tools' when grounding=False")
    else:
        results.fail("grounding=False should not have 'tools'")

    # thinkingConfig が正しいこと
    thinking_config = payload_no_grounding.get("generationConfig", {}).get("thinkingConfig", {})
    if thinking_config.get("thinkingLevel") == "High":
        results.ok("thinkingLevel='High' set correctly")
    else:
        results.fail("thinkingLevel", f"expected 'High', got {thinking_config.get('thinkingLevel')}")

    if thinking_config.get("includeThoughts") is False:
        results.ok("includeThoughts=False set correctly")
    else:
        results.fail("includeThoughts", f"expected False, got {thinking_config.get('includeThoughts')}")

    # imageConfig が正しいこと
    image_config = payload_no_grounding.get("generationConfig", {}).get("imageConfig", {})
    if image_config.get("imageSize") == "2K":
        results.ok("imageSize='2K' set correctly")
    else:
        results.fail("imageSize", f"expected '2K', got {image_config.get('imageSize')}")

    if image_config.get("aspectRatio") == "16:9":
        results.ok("aspectRatio='16:9' set correctly")
    else:
        results.fail("aspectRatio", f"expected '16:9', got {image_config.get('aspectRatio')}")

    # グラウンディングあり
    payload_with_grounding = build_payload(
        prompt="テストプロンプト",
        image_size="4K",
        thinking_level="minimal",
        grounding=True,
    )

    # tools が存在すること
    if "tools" in payload_with_grounding:
        results.ok("'tools' present when grounding=True")
    else:
        results.fail("grounding=True should have 'tools'")
        return

    # googleSearch の構造確認
    tools = payload_with_grounding["tools"]
    if len(tools) == 1 and "googleSearch" in tools[0]:
        results.ok("googleSearch tool structure correct")
    else:
        results.fail("googleSearch tool structure", str(tools))

    search_types = tools[0].get("googleSearch", {}).get("searchTypes", {})
    if "webSearch" in search_types and "imageSearch" in search_types:
        results.ok("webSearch and imageSearch both present")
    else:
        results.fail("searchTypes", f"expected webSearch+imageSearch, got {search_types}")

    # minimal Thinking
    thinking_config_min = payload_with_grounding.get("generationConfig", {}).get("thinkingConfig", {})
    if thinking_config_min.get("thinkingLevel") == "minimal":
        results.ok("thinkingLevel='minimal' set correctly")
    else:
        results.fail("thinkingLevel=minimal", f"got {thinking_config_min.get('thinkingLevel')}")

    # 4K imageSize
    image_config_4k = payload_with_grounding.get("generationConfig", {}).get("imageConfig", {})
    if image_config_4k.get("imageSize") == "4K":
        results.ok("imageSize='4K' set correctly")
    else:
        results.fail("imageSize=4K", f"got {image_config_4k.get('imageSize')}")


# ============================================================
# Test 7: extract_image_from_response
# ============================================================

def test_extract_image_from_response(results):
    """APIレスポンスからの画像抽出ロジックを検証"""
    print("\n--- Test 7: extract_image_from_response ---")

    from generate_slide_with_retry import extract_image_from_response
    import base64

    # 正常なレスポンス（1つの画像パーツ）
    test_image_data = b"FAKE_PNG_DATA"
    encoded = base64.b64encode(test_image_data).decode('utf-8')

    response_single = {
        "candidates": [{
            "content": {
                "parts": [
                    {"inlineData": {"mimeType": "image/png", "data": encoded}}
                ]
            }
        }]
    }

    extracted = extract_image_from_response(response_single)
    if extracted == test_image_data:
        results.ok("Single image extraction correct")
    else:
        results.fail("Single image extraction", f"data mismatch")

    # 複数パーツ（テキスト + 画像）- 末尾の画像を採用
    first_image = b"FIRST_IMAGE"
    last_image = b"LAST_IMAGE"

    response_multi = {
        "candidates": [{
            "content": {
                "parts": [
                    {"text": "thinking output"},
                    {"inlineData": {"mimeType": "image/png", "data": base64.b64encode(first_image).decode()}},
                    {"text": "more thinking"},
                    {"inlineData": {"mimeType": "image/png", "data": base64.b64encode(last_image).decode()}},
                ]
            }
        }]
    }

    extracted_multi = extract_image_from_response(response_multi)
    if extracted_multi == last_image:
        results.ok("Multiple parts: last image selected correctly")
    else:
        results.fail("Multiple parts extraction", "did not select last image")

    # 空レスポンス
    empty_response = {"candidates": []}
    extracted_empty = extract_image_from_response(empty_response)
    if extracted_empty is None:
        results.ok("Empty response returns None")
    else:
        results.fail("Empty response", "expected None")

    # 画像なしレスポンス
    no_image_response = {
        "candidates": [{
            "content": {
                "parts": [{"text": "No image generated"}]
            }
        }]
    }
    extracted_no_image = extract_image_from_response(no_image_response)
    if extracted_no_image is None:
        results.ok("No-image response returns None")
    else:
        results.fail("No-image response", "expected None")


# ============================================================
# Test 8: extract_grounding_metadata
# ============================================================

def test_extract_grounding_metadata(results):
    """グラウンディングメタデータの抽出を検証"""
    print("\n--- Test 8: extract_grounding_metadata ---")

    from generate_slide_with_retry import extract_grounding_metadata

    # グラウンディングメタデータ付きレスポンス
    response_with_meta = {
        "candidates": [{
            "content": {"parts": [{"text": "test"}]},
            "groundingMetadata": {
                "imageSearchQueries": ["AI market trend 2025"],
                "groundingChunks": [
                    {"web": {"uri": "https://example.com/ai-market", "title": "AI Market Report"}}
                ],
                "searchEntryPoint": {"renderedContent": "<html>...</html>"}
            }
        }]
    }

    meta = extract_grounding_metadata(response_with_meta)
    if meta is not None:
        results.ok("Grounding metadata extracted successfully")
    else:
        results.fail("Grounding metadata extraction")
        return

    if "imageSearchQueries" in meta:
        results.ok("imageSearchQueries field present")
    else:
        results.fail("imageSearchQueries missing")

    if "groundingChunks" in meta:
        results.ok("groundingChunks field present")
    else:
        results.fail("groundingChunks missing")

    # グラウンディングメタデータなしレスポンス
    response_no_meta = {
        "candidates": [{
            "content": {"parts": [{"text": "test"}]}
        }]
    }

    meta_none = extract_grounding_metadata(response_no_meta)
    if meta_none is None:
        results.ok("No metadata returns None")
    else:
        results.fail("No metadata", "expected None")


# ============================================================
# Test 9: End-to-end Phase 2-3 Pipeline
# ============================================================

def test_e2e_phase2_to_phase3(results):
    """Phase 2 (JSON) → Phase 3 (プロンプト + grounding_map) のE2Eテスト"""
    print("\n--- Test 9: E2E Phase 2-3 Pipeline ---")

    tmpdir = tempfile.mkdtemp()
    try:
        # セッションディレクトリ構造を作成
        json_dir = os.path.join(tmpdir, "json")
        prompts_dir = os.path.join(tmpdir, "prompts")
        os.makedirs(json_dir)
        os.makedirs(prompts_dir)

        # slides_plan.json を書き出し
        plan_path = os.path.join(json_dir, "slides_plan.json")
        with open(plan_path, 'w', encoding='utf-8') as f:
            json.dump(SAMPLE_SLIDES_PLAN, f, ensure_ascii=False, indent=2)

        # ダミーのデザインガイドラインを作成
        guidelines_path = os.path.join(tmpdir, "design_guidelines.md")
        with open(guidelines_path, 'w', encoding='utf-8') as f:
            f.write("# テスト用デザインガイドライン\n\nプライマリカラー: #FF6600\n")

        # 1. validate_slides_json.py を実行
        import subprocess
        validate_result = subprocess.run(
            [sys.executable, os.path.join(SCRIPTS_DIR, "validate_slides_json.py"),
             "--file", plan_path],
            capture_output=True, text=True
        )

        if validate_result.returncode == 0:
            results.ok("validate_slides_json.py passed for test data")
        else:
            results.fail("validate_slides_json.py", validate_result.stdout + validate_result.stderr)

        # 2. generate_prompts_from_json.py を実行
        gen_result = subprocess.run(
            [sys.executable, os.path.join(SCRIPTS_DIR, "generate_prompts_from_json.py"),
             "--session-dir", tmpdir,
             "--json-file", "json/slides_plan.json",
             "--output-dir", "prompts",
             "--design-guidelines", guidelines_path,
             "--image-size", "2K"],
            capture_output=True, text=True
        )

        if gen_result.returncode == 0:
            results.ok("generate_prompts_from_json.py completed successfully")
        else:
            results.fail("generate_prompts_from_json.py", gen_result.stdout + gen_result.stderr)
            return

        # 3. プロンプトファイルが5つ生成されたことを確認
        prompt_files = [f for f in os.listdir(prompts_dir) if f.endswith('.txt')]
        if len(prompt_files) == 5:
            results.ok(f"Generated {len(prompt_files)} prompt files")
        else:
            results.fail(f"Prompt file count", f"expected 5, got {len(prompt_files)}: {prompt_files}")

        # 4. grounding_map.json が生成されたことを確認
        grounding_map_path = os.path.join(tmpdir, "grounding_map.json")
        if os.path.exists(grounding_map_path):
            results.ok("grounding_map.json generated")
        else:
            results.fail("grounding_map.json not generated")
            return

        # 5. grounding_map.json の内容を検証
        with open(grounding_map_path, 'r', encoding='utf-8') as f:
            gmap = json.load(f)

        grounding_on = sum(1 for v in gmap.values() if v)
        if grounding_on == 2:
            results.ok(f"Grounding ON for {grounding_on} slides (expected 2)")
        else:
            results.fail(f"Grounding ON count", f"expected 2, got {grounding_on}")

        # 6. プロンプトファイルに解像度が含まれていることを確認
        sample_prompt_file = os.path.join(prompts_dir, prompt_files[0])
        with open(sample_prompt_file, 'r', encoding='utf-8') as f:
            prompt_content = f.read()

        if "2752x1536" in prompt_content:
            results.ok("2K resolution (2752x1536) found in generated prompt")
        else:
            results.fail("Resolution in prompt", "2752x1536 not found")

    finally:
        shutil.rmtree(tmpdir)


# ============================================================
# Test 10: Model ID and Constants
# ============================================================

def test_model_constants(results):
    """モデルIDとAPI定数の正確性を検証"""
    print("\n--- Test 10: Model ID and Constants ---")

    from generate_slide_with_retry import MODEL_ID, API_BASE, VALID_IMAGE_SIZES, REQUEST_TIMEOUT

    if MODEL_ID == "gemini-3.1-flash-image-preview":
        results.ok(f"MODEL_ID = {MODEL_ID}")
    else:
        results.fail("MODEL_ID", f"expected 'gemini-3.1-flash-image-preview', got '{MODEL_ID}'")

    if "v1beta" in API_BASE:
        results.ok(f"API_BASE uses v1beta")
    else:
        results.fail("API_BASE", f"expected v1beta endpoint, got {API_BASE}")

    expected_sizes = {"512px", "1K", "2K", "4K"}
    if VALID_IMAGE_SIZES == expected_sizes:
        results.ok(f"VALID_IMAGE_SIZES = {sorted(expected_sizes)}")
    else:
        results.fail("VALID_IMAGE_SIZES", f"expected {expected_sizes}, got {VALID_IMAGE_SIZES}")

    if REQUEST_TIMEOUT == 120:
        results.ok(f"REQUEST_TIMEOUT = 120 (increased for Thinking)")
    else:
        results.fail("REQUEST_TIMEOUT", f"expected 120, got {REQUEST_TIMEOUT}")


# ============================================================
# Test 11: generate_slides_parallel grounding map loading
# ============================================================

def test_parallel_grounding_map_loading(results):
    """generate_slides_parallel.py の grounding_map 読み込みを検証"""
    print("\n--- Test 11: Parallel Grounding Map Loading ---")

    from generate_slides_parallel import load_grounding_map

    # ファイルが存在しない場合
    empty_map = load_grounding_map(None)
    if empty_map == {}:
        results.ok("load_grounding_map(None) returns {}")
    else:
        results.fail("load_grounding_map(None)", f"expected {{}}, got {empty_map}")

    empty_map2 = load_grounding_map("/nonexistent/path.json")
    if empty_map2 == {}:
        results.ok("load_grounding_map(nonexistent) returns {}")
    else:
        results.fail("load_grounding_map(nonexistent)", f"expected {{}}, got {empty_map2}")

    # 正常なファイル
    tmpdir = tempfile.mkdtemp()
    try:
        test_map = {"00_cover_01": False, "01_market_02": True}
        map_path = os.path.join(tmpdir, "grounding_map.json")
        with open(map_path, 'w') as f:
            json.dump(test_map, f)

        loaded = load_grounding_map(map_path)
        if loaded == test_map:
            results.ok("load_grounding_map loads valid JSON correctly")
        else:
            results.fail("load_grounding_map", f"expected {test_map}, got {loaded}")
    finally:
        shutil.rmtree(tmpdir)


# ============================================================
# Main
# ============================================================

def main():
    print("=" * 60)
    print("nano-banana Slide Generator v3 Flash - Feature Tests")
    print("=" * 60)

    results = TestResult()

    test_resolution_mapping(results)
    test_grounding_map_extraction(results)
    test_grounding_map_save_load(results)
    test_validate_grounding_field(results)
    test_template_resolution_rendering(results)
    test_build_payload(results)
    test_extract_image_from_response(results)
    test_extract_grounding_metadata(results)
    test_e2e_phase2_to_phase3(results)
    test_model_constants(results)
    test_parallel_grounding_map_loading(results)

    success = results.summary()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
