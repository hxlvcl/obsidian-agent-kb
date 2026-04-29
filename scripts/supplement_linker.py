"""supplement_linker.py — 补充观点链接插入脚本

扫描所有 Wiki 概念页，找到 `#### 来自《文章名》`，
在标题下一行插入 `- [[文章名]]`（如果还不存在）。
"""

import os
import re

VAULT = r"{{VAULT_PATH}}"


def scan_wiki_files(wiki_dir):
    files = []
    for dirpath, _, filenames in os.walk(wiki_dir):
        for fn in filenames:
            if fn.endswith(".md") and fn != "_index.md":
                files.append(os.path.join(dirpath, fn))
    return files


def main():
    if "{{VAULT_PATH}}" in VAULT:
        print("[ERROR] 请先设置 VAULT 路径")
        return

    wiki_dir = os.path.join(VAULT, "02-Wiki")
    wiki_files = scan_wiki_files(wiki_dir)
    total = 0

    for fp in wiki_files:
        with open(fp, "r", encoding="utf-8") as f:
            content = f.read()

        # 收集所有匹配位置（从后往前处理，避免偏移）
        matches = list(re.finditer(r"(####\s+来自《(.+?)》)\n", content))
        fixed_in_file = 0

        for m in reversed(matches):
            header = m.group(1)
            article = m.group(2)
            expected = f"- [[{article}]]"

            # 检查下一行
            pos = m.end()
            nl = content.find("\n", pos)
            if nl == -1:
                nl = len(content)
            next_line = content[pos:nl]

            if next_line.strip() == expected:
                continue

            # 从后往前插入
            content = content[:pos] + expected + "\n" + content[pos:]
            fixed_in_file += 1

        if fixed_in_file > 0:
            with open(fp, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  {os.path.relpath(fp, VAULT)}: {fixed_in_file} 条")
        total += fixed_in_file

    if total == 0:
        print("[OK] 所有补充观点已有链接")
    else:
        print(f"\n[OK] 共插入 {total} 条链接")


if __name__ == "__main__":
    main()
