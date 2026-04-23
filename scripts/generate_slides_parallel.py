#!/usr/bin/env python3
"""
nano-banana Slide Generator v4 - 並列スライド画像生成スクリプト
Phase 4: 複数のプロンプトファイルからスライド画像を並列生成

v4:
  - Gemini / OpenAI (gpt-image-2) 両対応（--provider）
  - スライドごとのグラウンディング制御（--grounding-map、Geminiのみ）
  - 解像度選択（--image-size、両プロバイダ共通ラベル）
  - Thinkingレベル制御（--thinking-level、Geminiのみ）
  - OpenAI時は参考画像・ロゴを自動で /images/edits にルーティング
"""

import os
import sys
import glob
import json
import argparse
import subprocess
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed


def parse_args():
    parser = argparse.ArgumentParser(
        description='Generate slides in parallel from prompt files (v4 - Gemini/OpenAI両対応)'
    )
    parser.add_argument('--prompts-dir', required=True, help='Directory containing prompt text files (*.txt)')
    parser.add_argument('--output-dir', required=True, help='Output directory for slide images')
    parser.add_argument('--api-key', required=True, help='API key (Gemini or OpenAI depending on --provider)')
    parser.add_argument('--provider', default='openai', choices=['gemini', 'openai'],
                        help='画像生成プロバイダ（デフォルト: openai）')
    parser.add_argument('--max-parallel', type=int, default=10,
                        help='並列数（OpenAI Tier3=10推奨、Tier5=20+、Gemini=20）')
    parser.add_argument('--max-retries', type=int, default=3, help='Maximum retries per slide (default: 3)')
    parser.add_argument('--logo', help='Logo image path to include in each slide generation')
    parser.add_argument('--image-size', default='2K', choices=['512px', '1K', '2K', '4K'], help='Output resolution (default: 2K)')
    # Gemini固有
    parser.add_argument('--thinking-level', default='High', choices=['minimal', 'High'],
                        help='[Gemini] Thinkingレベル（デフォルト: High）')
    parser.add_argument('--grounding-map', help='[Gemini] Path to grounding map JSON (slide_name → true/false)')
    # 共通
    parser.add_argument('--reference-image-map', help='Path to reference image map JSON (slide_name_pattern → image_path)')
    # OpenAI固有
    parser.add_argument('--quality', default='high', choices=['auto', 'low', 'medium', 'high'],
                        help='[OpenAI] 画質（デフォルト: high）')
    parser.add_argument('--input-fidelity', default='high', choices=['low', 'high'],
                        help='[OpenAI] 参考画像への忠実度（デフォルト: high）')
    parser.add_argument('--background', default='auto', choices=['auto', 'transparent', 'opaque'],
                        help='[OpenAI] 背景処理（デフォルト: auto）')
    return parser.parse_args()


def load_grounding_map(grounding_map_path):
    """
    グラウンディングマップを読み込む

    グラウンディングマップはslides_plan.jsonから自動生成されるJSONファイル。
    キーはスライドのベース名、値はtrue/false。

    Returns:
        dict: {slide_base_name: bool} のマップ。パスがNoneなら空dict。
    """
    if not grounding_map_path or not os.path.exists(grounding_map_path):
        return {}

    with open(grounding_map_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_reference_image_map(ref_map_path):
    """
    リファレンス画像マップを読み込む

    マップはスライド名パターン → 画像パスのJSON。
    キーにスライドのベース名を含むものがマッチする（部分一致）。

    Returns:
        dict: {pattern: image_path} のマップ。パスがNoneなら空dict。
    """
    if not ref_map_path or not os.path.exists(ref_map_path):
        return {}

    with open(ref_map_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_reference_image(slide_base: str, ref_map: dict) -> str:
    """スライド名に対応するリファレンス画像パスを検索（部分一致）"""
    if not ref_map:
        return None
    if slide_base in ref_map:
        return ref_map[slide_base]
    for pattern, image_path in ref_map.items():
        if pattern in slide_base or slide_base in pattern:
            return image_path
    return None


def generate_single_slide(prompt_file_path, output_path, api_key, max_retries,
                          script_path, logo_path, image_size, thinking_level,
                          grounding, reference_image_path=None,
                          provider='gemini', quality='high', input_fidelity='high',
                          background='auto'):
    """
    単一スライドを生成（generate_slide_with_retry.pyを呼び出し）

    Returns:
        tuple: (success: bool, prompt_file: str, output_file: str, error_msg: str)
    """
    try:
        with open(prompt_file_path, 'r', encoding='utf-8') as f:
            prompt = f.read()

        cmd = [
            'python3', script_path,
            '--provider', provider,
            '--prompt', prompt,
            '--output', output_path,
            '--api-key', api_key,
            '--max-retries', str(max_retries),
            '--image-size', image_size,
        ]
        if provider == 'gemini':
            cmd.extend(['--thinking-level', thinking_level])
            if grounding:
                cmd.append('--grounding')
        else:  # openai
            cmd.extend([
                '--quality', quality,
                '--input-fidelity', input_fidelity,
                '--background', background,
            ])
        if logo_path:
            cmd.extend(['--logo', logo_path])
        if reference_image_path:
            cmd.extend(['--reference-image', reference_image_path])

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=240)

        if result.returncode == 0:
            return (True, prompt_file_path, output_path, None)
        else:
            error_msg = result.stderr if result.stderr else result.stdout
            return (False, prompt_file_path, output_path, error_msg)

    except subprocess.TimeoutExpired:
        return (False, prompt_file_path, output_path, "Timeout (4 minutes)")
    except Exception as e:
        return (False, prompt_file_path, output_path, str(e))


def extract_slide_info(prompt_filename):
    """
    プロンプトファイル名から接頭辞とスライド番号を抽出
    """
    import re
    match = re.search(r'^(.+)_(\d+)\.txt$', prompt_filename)
    if match:
        return (match.group(1), match.group(2))
    return ("slide", "000")


def main():
    args = parse_args()

    model_label = "gemini-3.1-flash-image-preview" if args.provider == "gemini" else "gpt-image-2"

    print("=" * 70)
    print(f"Phase 4: Parallel Slide Generation (v4 - provider={args.provider})")
    print("=" * 70)
    print(f"Provider:          {args.provider}")
    print(f"Model:             {model_label}")
    print(f"Prompts directory: {args.prompts_dir}")
    print(f"Output directory:  {args.output_dir}")
    print(f"Image size:        {args.image_size}")
    if args.provider == "gemini":
        print(f"Thinking level:    {args.thinking_level}")
    else:
        print(f"Quality:           {args.quality}")
        print(f"Input fidelity:    {args.input_fidelity}")
        print(f"Background:        {args.background}")
    print(f"Max parallel:      {args.max_parallel}")
    print(f"Max retries:       {args.max_retries}")
    if args.logo:
        print(f"Logo:              {args.logo}")
    if args.grounding_map and args.provider == "gemini":
        print(f"Grounding map:     {args.grounding_map}")
    if args.reference_image_map:
        print(f"Ref image map:     {args.reference_image_map}")
    print("=" * 70)

    os.makedirs(args.output_dir, exist_ok=True)

    prompt_files = sorted(
        glob.glob(os.path.join(args.prompts_dir, '*.txt')),
        key=lambda x: extract_slide_info(os.path.basename(x))[1]
    )

    if not prompt_files:
        print(f"Error: No prompt files (*.txt) found in {args.prompts_dir}")
        sys.exit(1)

    grounding_map = load_grounding_map(args.grounding_map)
    ref_image_map = load_reference_image_map(args.reference_image_map)

    grounding_on_count = sum(1 for v in grounding_map.values() if v)
    print(f"\nFound {len(prompt_files)} prompt files")
    if grounding_map:
        print(f"Grounding enabled for {grounding_on_count}/{len(prompt_files)} slides")
    if ref_image_map:
        print(f"Reference images: {len(ref_image_map)} pattern(s) configured")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    retry_script = os.path.join(script_dir, 'generate_slide_with_retry.py')

    if not os.path.exists(retry_script):
        print(f"Error: {retry_script} not found")
        sys.exit(1)

    tasks = []
    for prompt_file in prompt_files:
        prefix, slide_num = extract_slide_info(os.path.basename(prompt_file))
        output_filename = f"{prefix}_{slide_num}.png"
        output_path = os.path.join(args.output_dir, output_filename)

        slide_base = f"{prefix}_{slide_num}"
        slide_grounding = grounding_map.get(slide_base, False)
        slide_ref_image = find_reference_image(slide_base, ref_image_map)

        tasks.append((
            prompt_file, output_path, args.api_key, args.max_retries,
            retry_script, args.logo, args.image_size, args.thinking_level,
            slide_grounding, slide_ref_image,
            args.provider, args.quality, args.input_fidelity, args.background,
        ))

    print(f"\nGenerating {len(tasks)} slides with {args.max_parallel} parallel workers...")
    print("=" * 70)

    success_count = 0
    failed_slides = []

    with ProcessPoolExecutor(max_workers=args.max_parallel) as executor:
        future_to_task = {
            executor.submit(generate_single_slide, *task): task
            for task in tasks
        }

        completed = 0
        for future in as_completed(future_to_task):
            completed += 1
            success, prompt_file, output_file, error_msg = future.result()

            if success:
                success_count += 1
                print(f"✓ [{completed}/{len(tasks)}] {os.path.basename(output_file)}")
            else:
                failed_slides.append((prompt_file, output_file, error_msg))
                print(f"✗ [{completed}/{len(tasks)}] {os.path.basename(output_file)} - {error_msg}")

    print("\n" + "=" * 70)
    print("Generation Summary")
    print("=" * 70)
    print(f"Total slides:           {len(tasks)}")
    print(f"Successfully generated: {success_count}")
    print(f"Failed:                 {len(failed_slides)}")
    print("=" * 70)

    if failed_slides:
        print("\nFailed slides:")
        for prompt_file, output_file, error_msg in failed_slides:
            print(f"  - {os.path.basename(prompt_file)}: {error_msg}")
        print("\nYou can retry failed slides manually using regenerate_slide.py")
        sys.exit(1)
    else:
        print("\n✓ All slides generated successfully!")
        return 0


if __name__ == '__main__':
    sys.exit(main())
