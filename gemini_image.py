"""
Gemini 社群貼文自動配圖
用法：python gemini_image.py
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path
from google import genai
from google.genai import types

API_KEY = os.environ.get("GEMINI_API_KEY", "")
OUTPUT_DIR = Path(__file__).parent / "100_Todo" / "drafts" / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PROMPT_TEMPLATE = """你是一位專業的社群圖片 prompt 工程師。
根據以下繁體中文貼文內容，生成一段適合 Imagen 3 的英文圖片 prompt。

規則：
- 純英文，100 字以內
- 風格：現代、乾淨、商業感，適合 Facebook / Instagram
- 不要人臉（避免版權與審查問題）
- 呈現貼文核心概念或氛圍
- 只輸出 prompt，不要解釋

貼文內容：
{post_text}
"""


def get_image_prompt(client: genai.Client, post_text: str) -> str:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=PROMPT_TEMPLATE.format(post_text=post_text),
    )
    return response.text.strip()


def generate_image(client: genai.Client, image_prompt: str, filename: str) -> Path:
    response = client.models.generate_images(
        model="imagen-4.0-generate-001",
        prompt=image_prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio="3:4",  # IG/FB 直式
            person_generation="DONT_ALLOW",
        ),
    )

    image_data = response.generated_images[0].image.image_bytes
    output_path = OUTPUT_DIR / filename
    output_path.write_bytes(image_data)
    return output_path


def slugify(text: str, max_len: int = 30) -> str:
    text = re.sub(r"[^\w一-鿿]+", "_", text)
    return text[:max_len].strip("_")


def main():
    if not API_KEY:
        print("錯誤：請先設定環境變數 GEMINI_API_KEY")
        sys.exit(1)

    client = genai.Client(api_key=API_KEY)

    print("=== Gemini 社群貼文自動配圖 ===")
    print("請貼入貼文內容（輸入完畢後按 Enter 兩次）：\n")

    lines = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    post_text = "\n".join(lines).strip()

    if not post_text:
        print("錯誤：貼文內容不能為空")
        sys.exit(1)

    print("\n生成圖片 prompt 中...")
    image_prompt = get_image_prompt(client, post_text)
    print(f"Image prompt：{image_prompt}\n")

    date_str = datetime.now().strftime("%Y-%m-%d_%H%M")
    slug = slugify(post_text[:20])
    filename = f"{date_str}_{slug}.png"

    print("生成圖片中（約需 10-20 秒）...")
    output_path = generate_image(client, image_prompt, filename)

    print(f"\n完成！圖片已存至：\n{output_path}")


if __name__ == "__main__":
    main()
