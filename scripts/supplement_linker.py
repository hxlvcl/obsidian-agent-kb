"""supplement_linker.py — 补充观点链接插入+验证脚本

扫描所有 Wiki 概念页，找到 `#### 来自《文章名》`，
解析为完整文件名后在标题下一行插入 `- [[完整文件名]]`。
"""

import os
import re

VAULT = r"{{VAULT_PATH}}"


def build_name_index(vault):
    """返回 {前缀: 完整文件名} 映射"""
    index = {}
    for root, _, fns in os.walk(vault):
        for fn in fns:
            if fn.endswith(".md"):
                index[fn] = fn
    return index


def resolve_article(header_text, name_index):
    """用 #### 来自《》里的短名解析完整文件名"""
    # 先精确匹配
    exact = header_text + ".md"
    if exact in name_index:
        return exact[:-3]  # 去掉 .md

    # 前缀匹配 — 找最优（最长前缀胜出）
    candidates = []
    for full in name_index:
        if full.startswith(header_text):
            candidates.append(full[:-3])
    if candidates:
        return max(candidates, key=len)
    return None


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
    name_index = build_name_index(VAULT)
    total = 0
    unresolvable = []

    for fp in wiki_files:
        with open(fp, "r", encoding="utf-8") as f:
            content = f.read()

        matches = list(re.finditer(r"####\s+来自《(.+?)》\n", content))
        fixed_in_file = 0

        for m in reversed(matches):
            header_text = m.group(1)
            full_name = resolve_article(header_text, name_index)

            if full_name is None:
                unresolvable.append((os.path.relpath(fp, VAULT), header_text))
                continue

            expected = f"- [[{full_name}]]"
            pos = m.end()
            nl = content.find("\n", pos)
            if nl == -1:
                nl = len(content)
            next_line = content[pos:nl]

            if next_line.strip() == expected:
                continue

            content = content[:pos] + expected + "\n" + content[pos:]
            fixed_in_file += 1

        if fixed_in_file > 0:
            with open(fp, "w", encoding="utf-8") as f:
                f.write(content)
            rel = os.path.relpath(fp, VAULT).replace("\\", "/")
            print(f"  {rel}: {fixed_in_file} 条")
        total += fixed_in_file

    if total == 0:
        print("[OK] 所有补充观点已有链接")
    else:
        print(f"\n[OK] 共插入 {total} 条链接")

    if unresolvable:
        print(f"\n--- 无法解析 ({len(unresolvable)} 条) ---")
        for wiki_page, header in unresolvable:
            print(f"  {wiki_page}: 《{header}》")

    # 验证（路径改成全库扫描）
    print("\n--- 验证链接 ---")
    broken = 0
    for fp in wiki_files:
        with open(fp, "r", encoding="utf-8") as f:
            c = f.read()
        supp = c.find("### 补充观点")
        if supp < 0:
            continue
        for m in re.finditer(r"\[\[(.+?)\]\]", c[supp:]):
            link = m.group(1)
            full = link + ".md"
            if full not in name_index:
                rel = os.path.relpath(fp, VAULT).replace("\\", "/")
                print(f"  [BLANK] {rel}: [[{link}]]")
                broken += 1

    if broken == 0:
        print("  [OK] 无悬空链接")
    else:
        print(f"\n  [WARN] 共 {broken} 条悬空链接，请手动修正")


if __name__ == "__main__":
    main()
