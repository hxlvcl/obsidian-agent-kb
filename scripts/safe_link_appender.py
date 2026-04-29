"""safe_link_appender.py — 知识库链接安全追加脚本

白名单+黑名单机制，确保入库流程中不会意外修改只读区文章。

用法：
    # 新文章建链（仅 00-收件箱/）
    python safe_link_appender.py --new-article --target "00-收件箱/xxx.md" --links "文件名1,文件名2"

    # Wiki 概念页追加关联文章（仅 02-Wiki/）
    python safe_link_appender.py --wiki-concept --target "02-Wiki/01-科技/Skill生态.md" --article "新文章标题"

    # _index.md 追加索引条目（仅 02-Wiki/_index.md）
    python safe_link_appender.py --wiki-index --category "01-科技" --entry "[[新文章]] — 摘要"

安全规则：
    白名单：00-收件箱/、02-Wiki/
    黑名单：01-素材库/、03-思考/、04-项目/、05-产出/、06-系统/
    触之即拒，绝无不写。
"""

import argparse
import os
import re
import sys

VAULT = r"D:\Obsidian知识库\知识库"
ALLOWED = [r"00-收件箱", r"02-Wiki"]
BLOCKED = [r"01-素材库", r"03-思考", r"04-项目", r"05-产出", r"06-系统"]


def is_allowed(path):
    """Check if path is in allowed directory."""
    rel = os.path.relpath(path, VAULT)
    for prefix in BLOCKED:
        if rel.replace("\\", "/").startswith(prefix.replace("\\", "/")):
            return False, f"BLOCKED: '{rel}' 在禁止写入目录 '{prefix}'"
    for prefix in ALLOWED:
        if rel.replace("\\", "/").startswith(prefix.replace("\\", "/")):
            return True, ""
    return False, f"BLOCKED: '{rel}' 不在白名单目录"


def new_article(target, links):
    """替换或追加 00-收件箱/ 文章中的关联文章链接（支持多次调用累积）"""
    ok, err = is_allowed(target)
    if not ok:
        print(f"[REJECT] {err}")
        return False

    # 问题4：禁止 --new-article 碰 _index.md
    if os.path.basename(target) == "_index.md":
        print(f"[REJECT] _index.md 只能通过 --wiki-index 修改")
        return False

    try:
        with open(target, "r", encoding="utf-8") as f:
            content = f.read()
    except (IOError, PermissionError) as e:
        print(f"[ERROR] 读取失败：{target} — {e}")
        return False

    new_links = [l.strip() for l in links.split(",") if l.strip()]

    placeholder = "（待统一建链）"

    if placeholder in content:
        # 首次建链：替换占位符
        items = "\n".join([f"[[{l}]]" for l in new_links])
        content = content.replace(placeholder, items, 1)

    else:
        # 已有 **关联文章** 区块：解析已有链接，合并去重后追加
        block_match = re.search(r"\*\*关联文章\*\*\n\n((?:\[\[.+?\]\]\n?)+)", content)
        if block_match:
            existing_block = block_match.group(0)
            existing_links = re.findall(r"\[\[(.+?)\]\]", existing_block)
            # 合并去重，保持顺序
            seen = set(existing_links)
            added = [l for l in new_links if l not in seen]
            if not added:
                print(f"[INFO] 链接已存在，跳过：{new_links}")
                return True
            merged = existing_links + added
            merged_items = "\n".join([f"[[{l}]]" for l in merged])
            new_block = f"**关联文章**\n\n{merged_items}"
            content = content.replace(existing_block, new_block, 1)
            new_links = added  # 只报告新增的

        else:
            # 无占位符也无区块 → 末尾新建
            items = "\n".join([f"[[{l}]]" for l in new_links])
            content = content.rstrip() + f"\n\n**关联文章**\n\n{items}\n"

    try:
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
    except (IOError, PermissionError) as e:
        print(f"[ERROR] 写入失败：{target} — {e}")
        return False

    print(f"[OK] 已写入关联文章：{target} → {new_links}")
    return True


def wiki_concept(target, article):
    """在 Wiki 概念页的 **关联文章** 区块内追加链接"""
    ok, err = is_allowed(target)
    if not ok:
        print(f"[REJECT] {err}")
        return False

    # 问题4：禁止 --wiki-concept 碰 _index.md
    if os.path.basename(target) == "_index.md":
        print(f"[REJECT] _index.md 只能通过 --wiki-index 修改")
        return False

    try:
        with open(target, "r", encoding="utf-8") as f:
            content = f.read()
    except (IOError, PermissionError) as e:
        print(f"[ERROR] 读取失败：{target} — {e}")
        return False

    line = f"- [[{article}]]"

    # 找到 **关联文章** 区块，在区块内追加
    block_match = re.search(r"\*\*关联文章\*\*((?:\n.*?)*?)(?=\n## |\n---|\Z)", content, re.DOTALL)
    if block_match:
        block_start = block_match.start()
        block_end = block_match.end()
        block_text = block_match.group(0)
        # 去掉占位符，追加新链接
        block_text = block_text.replace("（待统一建链）", "")
        block_text = block_text.rstrip()
        block_text += f"\n{line}"
        content = content[:block_start] + block_text + content[block_end:]
    else:
        # 没有区块 → 末尾新建
        content = content.rstrip() + f"\n\n**关联文章**\n\n{line}\n"

    try:
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
    except (IOError, PermissionError) as e:
        print(f"[ERROR] 写入失败：{target} — {e}")
        return False

    print(f"[OK] Wiki 概念页已追加：{target} ← {article}")
    return True


def wiki_index(category, entry):
    """在 _index.md 对应分类末尾追加索引条目（问题3：不依赖占位符，不产生多余空行）"""
    target = os.path.join(VAULT, "02-Wiki", "_index.md")
    ok, err = is_allowed(target)
    if not ok:
        print(f"[REJECT] {err}")
        return False

    try:
        with open(target, "r", encoding="utf-8") as f:
            content = f.read()
    except (IOError, PermissionError) as e:
        print(f"[ERROR] 读取失败：{target} — {e}")
        return False

    cat_header = f"## {category}"
    if cat_header not in content:
        print(f"[ERROR] _index.md 中未找到分类：{cat_header}")
        return False

    # 找到下一个分类标题或文件末尾
    cat_pos = content.index(cat_header)
    after_header = content.index("\n", cat_pos) + 1
    next_cat = content.find("\n## ", after_header)
    if next_cat == -1:
        next_cat = len(content)

    # 问题3：掐掉分类末尾多余空行再插入
    prefix = content[:next_cat].rstrip()
    suffix = content[next_cat:]
    content = prefix + f"\n- {entry}\n" + suffix

    try:
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
    except (IOError, PermissionError) as e:
        print(f"[ERROR] 写入失败：{target} — {e}")
        return False

    print(f"[OK] _index.md 追加条目：{category} → {entry}")
    return True


def main():
    parser = argparse.ArgumentParser(description="安全链接追加脚本")
    parser.add_argument("--new-article", action="store_true", help="新文章建链模式")
    parser.add_argument("--wiki-concept", action="store_true", help="Wiki概念页追加模式")
    parser.add_argument("--wiki-index", action="store_true", help="_index.md追加模式")
    parser.add_argument("--target", type=str, help="目标文件路径（相对或绝对）")
    parser.add_argument("--links", type=str, help="关联文件名，逗号分隔")
    parser.add_argument("--article", type=str, help="新文章标题（wiki概念页模式）")
    parser.add_argument("--category", type=str, help="Wiki分类（如 01-科技）")
    parser.add_argument("--entry", type=str, help="_index.md条目，格式 [[文章]] — 摘要")

    args = parser.parse_args()

    if args.new_article:
        if not args.target or not args.links:
            print("[ERROR] --new-article 需要 --target 和 --links")
            sys.exit(1)
        target = os.path.join(VAULT, args.target) if not os.path.isabs(args.target) else args.target
        ok = new_article(target, args.links)
    elif args.wiki_concept:
        if not args.target or not args.article:
            print("[ERROR] --wiki-concept 需要 --target 和 --article")
            sys.exit(1)
        target = os.path.join(VAULT, args.target) if not os.path.isabs(args.target) else args.target
        ok = wiki_concept(target, args.article)
    elif args.wiki_index:
        if not args.category or not args.entry:
            print("[ERROR] --wiki-index 需要 --category 和 --entry")
            sys.exit(1)
        ok = wiki_index(args.category, args.entry)
    else:
        print("[ERROR] 需要指定 --new-article / --wiki-concept / --wiki-index")
        sys.exit(1)

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
