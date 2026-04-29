"""supplement_linker.py — 补充观点自动回链脚本

扫描所有 Wiki 概念页，找到 `#### 来自《文章名》` 的补充观点，
检查对应的 [[文章名]] 是否已在页面的 **关联文章** 区块中。
如不在，自动追加 wiki-concept 回链。

用于阶段三步 15 之前执行，保证补充观点不漏链。
"""

import os
import re
import subprocess
import sys

VAULT = r"{{VAULT_PATH}}"
WIKI_DIR = os.path.join(VAULT, "02-Wiki")
SCRIPT = "scripts/safe_link_appender.py"


def scan_wiki_files():
    """扫描所有 Wiki 概念页（不含 _index.md）"""
    files = []
    for dirpath, _, filenames in os.walk(WIKI_DIR):
        for fn in filenames:
            if fn.endswith(".md") and fn != "_index.md":
                files.append(os.path.join(dirpath, fn))
    return files


def extract_supplement_articles(content):
    """提取 #### 来自《文章名》中的文章名称"""
    articles = []
    for m in re.finditer(r"####\s+来自《(.+?)》", content):
        articles.append(m.group(1))
    return articles


def extract_linked_articles(content):
    """提取 **关联文章** 区块中的所有 [[链接]]"""
    block = re.search(r"\*\*关联文章\*\*(.*?)(?=\n#{2,3} |\n---|\Z)", content, re.DOTALL)
    if not block:
        return set()
    links = re.findall(r"\[\[(.+?)\]\]", block.group(0))
    # 同时匹配 - [[...]] 格式
    dash_links = re.findall(r"- \[\[(.+?)\]\]", block.group(0))
    return set(links) | set(dash_links)


def main():
    if "{{VAULT_PATH}}" in VAULT:
        print("[ERROR] 请先设置 VAULT 路径")
        return

    wiki_files = scan_wiki_files()
    missing = []

    for fp in wiki_files:
        with open(fp, "r", encoding="utf-8") as f:
            content = f.read()

        supplement_articles = extract_supplement_articles(content)
        linked_articles = extract_linked_articles(content)

        rel = os.path.relpath(fp, VAULT)
        for article in supplement_articles:
            if article not in linked_articles:
                missing.append((rel, article))

    if not missing:
        print("✅ 所有补充观点已回链")
        return

    print(f"🔗 发现 {len(missing)} 条缺失回链：\n")
    for wiki_page, article in missing:
        print(f"  {wiki_page} ← {article}")

    # 自动补链
    print("\n--- 自动补链 ---")
    for wiki_page, article in missing:
        target = os.path.join(VAULT, wiki_page)
        result = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), SCRIPT),
             "--wiki-concept", "--target", target, "--article", article],
            capture_output=True, text=True, cwd=VAULT
        )
        print(f"  {result.stdout.strip()}")

    print(f"\n✅ 完成 {len(missing)} 条回链")


if __name__ == "__main__":
    main()
