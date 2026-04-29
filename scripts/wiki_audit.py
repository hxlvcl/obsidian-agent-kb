"""wiki_audit.py — Wiki 定期体检脚本

检查 Wiki 的结构性健康问题：
1. 空洞页：只有标题没有实质内容
2. 孤立页：没有任何其他文章链接到它
3. 断链：正文中 [[链接]] 指向不存在的文件
4. 频繁提及但无独立页面的概念：在素材库中多次被 [[提及]]，但 Wiki 里没有
5. 过时的 _index.md 条目：索引引用了不存在的文件

输出：JSON 报告 + Markdown 可读摘要
AI Agent 拿到报告后再做语义层面的检查（冲突定义、过期结论）。

用法：
    python wiki_audit.py
    python wiki_audit.py --output report.md
    python wiki_audit.py --json
"""

import argparse
import json
import os
import re
import sys
from collections import Counter

VAULT = r"{{VAULT_PATH}}"
WIKI_DIR = os.path.join(VAULT, "02-Wiki")
SUCAI_DIR = os.path.join(VAULT, "01-素材库")
INDEX_FILE = os.path.join(WIKI_DIR, "_index.md")

# 正文最少字符数，低于此值视为空洞页
MIN_CONTENT_CHARS = 200


def scan_all_files(root_dir, ext=".md"):
    """扫描目录下所有 md 文件，忽略 _index.md"""
    files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for fn in filenames:
            if fn.endswith(ext) and fn != "_index.md":
                files.append(os.path.join(dirpath, fn))
    return files


def extract_body(filepath):
    """提取正文（去掉 frontmatter）"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except (IOError, PermissionError):
        return ""

    if content.startswith("---"):
        match = re.search(r"^---\n(.*?)\n---\n", content, re.DOTALL)
        if match:
            return content[match.end():]
    return content


def extract_all_links(text):
    """提取所有 [[链接]]，返回文件名列表（去掉别名和#锚点）"""
    links = re.findall(r"\[\[(.+?)\]\]", text)
    cleaned = []
    for link in links:
        # 去掉 #锚点、|别名
        name = link.split("#")[0].split("|")[0]
        cleaned.append(name)
    return cleaned


def check_empty_pages(wiki_files):
    """空洞页：正文内容过少"""
    results = []
    for fp in wiki_files:
        body = extract_body(fp).strip()
        # 去掉空行、标题行、分隔线
        real_content = re.sub(r"^#+\s.*$", "", body, flags=re.MULTILINE)
        real_content = re.sub(r"^---+$", "", real_content, flags=re.MULTILINE)
        real_content = real_content.strip()
        if len(real_content) < MIN_CONTENT_CHARS:
            rel = os.path.relpath(fp, WIKI_DIR)
            results.append({"file": rel, "content_chars": len(real_content)})
    return results


def check_orphan_pages(wiki_files, all_links):
    """孤立页：没有任何其他文件链接到它"""
    # 收集所有被链接的文件名
    linked_to = set()
    for target in all_links:
        linked_to.add(target)

    orphans = []
    for fp in wiki_files:
        name = os.path.splitext(os.path.basename(fp))[0]
        if name not in linked_to:
            rel = os.path.relpath(fp, WIKI_DIR)
            orphans.append({"file": rel, "title": name})
    return orphans


def check_broken_links(all_files, all_links):
    """断链：指向不存在的文件"""
    # 收集所有存在的文件名（含素材库）
    existing = set()
    for fp in all_files:
        name = os.path.splitext(os.path.basename(fp))[0]
        existing.add(name)

    broken = []
    for fp in all_files:
        body = extract_body(fp)
        links = extract_all_links(body)
        for link in links:
            if link not in existing:
                broken.append({
                    "source": os.path.relpath(fp, VAULT),
                    "broken_link": link
                })
    return broken


def check_missing_concepts(wiki_files, sucai_files):
    """频繁提及但无独立页面的概念"""
    # 收集 Wiki 中已有的概念名
    wiki_concepts = set()
    for fp in wiki_files:
        wiki_concepts.add(os.path.splitext(os.path.basename(fp))[0])

    # 统计素材库中 [[提及]] 的频率
    mentions = Counter()
    for fp in sucai_files:
        body = extract_body(fp)
        links = extract_all_links(body)
        for link in links:
            mentions[link] += 1

    # 被提及 >=2 次、不在 Wiki 中的
    missing = []
    for concept, count in mentions.most_common(50):
        if concept not in wiki_concepts and count >= 2:
            missing.append({"concept": concept, "mentions": count})
    return missing


def check_stale_index():
    """检查 _index.md 中引用的条目是否还存在"""
    if not os.path.exists(INDEX_FILE):
        return []

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    index_links = extract_all_links(content)
    stale = []
    for link in index_links:
        # 检查 Wiki 和素材库中是否有这个文件
        found = False
        for root_dir in [WIKI_DIR, SUCAI_DIR]:
            for dirpath, _, filenames in os.walk(root_dir):
                if f"{link}.md" in filenames:
                    found = True
                    break
            if found:
                break
        if not found:
            stale.append({"index_entry": link})

    return stale


def generate_report(json_output=False):
    """生成完整报告"""
    wiki_files = scan_all_files(WIKI_DIR)
    sucai_files = scan_all_files(SUCAI_DIR)
    all_files = wiki_files + sucai_files

    # 收集所有链接
    all_links = []
    for fp in all_files:
        body = extract_body(fp)
        all_links.extend(extract_all_links(body))

    report = {
        "empty_pages": check_empty_pages(wiki_files),
        "orphan_pages": check_orphan_pages(wiki_files, all_links),
        "broken_links": check_broken_links(all_files, all_links),
        "missing_concepts": check_missing_concepts(wiki_files, sucai_files),
        "stale_index": check_stale_index(),
        "summary": {
            "total_wiki_pages": len(wiki_files),
            "total_sucai_files": len(sucai_files),
            "total_links": len(all_links),
        }
    }

    return report


def format_report(report):
    """格式化 Markdown 报告"""
    lines = []
    lines.append("# Wiki 体检报告")
    lines.append("")
    lines.append(f"- Wiki 页数：{report['summary']['total_wiki_pages']}")
    lines.append(f"- 素材库文件数：{report['summary']['total_sucai_files']}")
    lines.append(f"- 总链接数：{report['summary']['total_links']}")
    lines.append("")

    # 空洞页
    lines.append("## 🔴 空洞页（正文 < 200 字符）")
    if report["empty_pages"]:
        for item in report["empty_pages"]:
            lines.append(f"- `{item['file']}` — {item['content_chars']} 字符")
    else:
        lines.append("✅ 无")
    lines.append("")

    # 孤立页
    lines.append("## 🟡 孤立页（无其他文章链接到它）")
    if report["orphan_pages"]:
        for item in report["orphan_pages"]:
            lines.append(f"- `{item['file']}`")
    else:
        lines.append("✅ 无")
    lines.append("")

    # 断链
    lines.append("## 🔴 断链（指向不存在文件）")
    if report["broken_links"]:
        for item in report["broken_links"]:
            lines.append(f"- `{item['source']}` → `[[{item['broken_link']}]]`")
    else:
        lines.append("✅ 无")
    lines.append("")

    # 缺失概念
    lines.append("## 🔵 频繁提及但无独立页面（素材库中 ≥2 次提及）")
    if report["missing_concepts"]:
        for item in report["missing_concepts"]:
            lines.append(f"- `{item['concept']}` — 被提及 {item['mentions']} 次")
    else:
        lines.append("✅ 无")
    lines.append("")

    # 过时索引
    lines.append("## 🟡 _index.md 过时条目（引用不存在的文件）")
    if report["stale_index"]:
        for item in report["stale_index"]:
            lines.append(f"- `[[{item['index_entry']}]]`")
    else:
        lines.append("✅ 无")
    lines.append("")

    lines.append("---")
    lines.append("*报告由 wiki_audit.py 自动生成，AI Agent 还需检查：冲突定义、过期结论、语义矛盾*")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Wiki 定期体检脚本")
    parser.add_argument("--output", type=str, help="输出 Markdown 报告文件路径")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    args = parser.parse_args()

    if "{{VAULT_PATH}}" in VAULT:
        print("[ERROR] 请先将 VAULT 变量改为你的 Obsidian Vault 路径")
        sys.exit(1)

    report = generate_report()

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        output = format_report(report)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"[OK] 报告已保存：{args.output}")
        else:
            print(output)


if __name__ == "__main__":
    main()
