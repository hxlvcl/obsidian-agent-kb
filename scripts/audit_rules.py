#!/usr/bin/env python3
"""
audit_rules.py -- 规则自检脚本

功能：
1. 扫描 04-项目/错误日志.md，提取所有验证失败记录
2. 按类型/原因聚类分析，找出高频错误
3. 为每条高频错误生成规则改进建议
4. 输出报告

用法：
  python scripts/audit_rules.py             # 扫描并输出报告
  python scripts/audit_rules.py --save      # 保存报告到文件
"""

import re
import sys
from pathlib import Path
from datetime import datetime

VAULT_DIR = Path("{{VAULT_PATH}}")
ERROR_LOG = VAULT_DIR / "04-项目" / "错误日志.md"


def parse_error_log():
    """解析错误日志（markdown格式，按日期分组），返回记录列表"""
    if not ERROR_LOG.exists():
        print("[ERROR] 错误日志不存在：%s" % ERROR_LOG)
        return []

    text = ERROR_LOG.read_text(encoding="utf-8")

    # Remove code blocks (the format example shouldn't be parsed as records)
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)

    # Find the first date header "## YYYY-MM-DD", remove everything before it
    date_match = re.search(r"(?m)^## \d{4}-\d{2}-\d{2}", text)
    if date_match:
        text = text[date_match.start():]
    else:
        # Fallback: look for old "## 记录" marker
        records_start = text.find("## 记录")
        if records_start >= 0:
            text = text[records_start:]
        else:
            return []

    # Split by "### " headings (across all date sections)
    blocks = re.split(r"(?m)^### ", text)
    records = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = block.split("\n")
        heading = lines[0].strip()
        if heading in ("", "记录") or heading.startswith("<!--"):
            continue

        record = {"_heading": heading}
        for line in lines[1:]:
            line = line.strip()
            if not line or line.startswith("<!--"):
                continue
            # Parse "**key**：value" or "**key**: value"
            m = re.match(r'\*\*(.+?)\*\*[:：]\s*(.+)', line)
            if m:
                record[m.group(1)] = m.group(2).strip()

        if len(record) > 1:  # Has at least heading + one field
            records.append(record)

    return records


def analyze_errors(records):
    """聚类分析错误记录"""
    if not records:
        return {"total": 0, "by_type": {}, "by_operation": {}, "unresolved": []}

    by_type = {}
    by_operation = {}
    unresolved = []

    for r in records:
        t = r.get("_heading", "未知")
        op = r.get("操作", "未知")
        status = r.get("状态", "")
        by_type[t] = by_type.get(t, 0) + 1
        by_operation[op] = by_operation.get(op, 0) + 1
        if status in ("未解决", "待确认", ""):
            unresolved.append(r)

    return {
        "total": len(records),
        "by_type": by_type,
        "by_operation": by_operation,
        "unresolved": unresolved,
    }


def generate_suggestions(analysis):
    """生成规则改进建议"""
    suggestions = []

    if analysis["total"] == 0:
        suggestions.append("[OK] 错误日志为空，无需规则调整。")
        return suggestions

    # 提取所有不重复的原因做分类建议
    causes_seen = set()
    for r in analysis["unresolved"]:
        cause = r.get("原因", "")
        if not cause or cause in causes_seen:
            continue
        causes_seen.add(cause)
        cause_short = cause[:60]

        if "格式" in cause or "字段" in cause:
            suggestions.append(
                "[格式] `%s...`" % cause_short
                + "\n    -> 建议补充格式校验规则到知识库管理指南.md 或 AGENTS.md"
            )
        elif "链接" in cause or "双链" in cause:
            suggestions.append(
                "[链接] `%s...`" % cause_short
                + "\n    -> 建议在知识库管理指南.md 补充双链格式示例"
            )
        elif "模板" in cause or "frontmatter" in cause.lower():
            suggestions.append(
                "[模板] `%s...`" % cause_short
                + "\n    -> 建议更新 06-系统/模板/新笔记.md 的示例"
            )
        elif "移动" in cause or "目录" in cause:
            suggestions.append(
                "[路径] `%s...`" % cause_short
                + "\n    -> 建议检查目标目录是否存在、路径书写是否正确"
            )
        elif "回滚" in cause or "git" in cause.lower():
            suggestions.append(
                "[Git] `%s...`" % cause_short
                + "\n    -> 建议检查 git_control.py 状态"
            )
        else:
            suggestions.append(
                "[其他] `%s...`" % cause_short
                + "\n    -> 建议人工审查该记录"
            )

    # 识别高频错误类型
    for t, c in sorted(analysis["by_type"].items(), key=lambda x: -x[1]):
        if c >= 2:
            suggestions.append(
                "[WARN] `%s` 类错误出现 %d 次，存在模式化问题，" % (t, c)
                + "\n   建议重点检查相关流程步骤是否描述清晰"
            )

    if not suggestions:
        suggestions.append("[OK] 未发现明显的规则缺口，建议人工审查未解决的记录。")

    return suggestions


def print_report(analysis, suggestions):
    """输出分析报告到终端"""
    print("=" * 65)
    print("  [规则自检报告]")
    print("  扫描时间：%s" % datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("=" * 65)

    print("\n[统计] 总记录数：%d" % analysis["total"])

    if analysis["total"] > 0:
        print("\n[按错误类型分布]：")
        for t, c in sorted(analysis["by_type"].items(), key=lambda x: -x[1]):
            bar = "#" * min(c * 3, 30)
            print("   %s  %s: %d 次" % (bar, t, c))

        print("\n[按操作分布]：")
        for op, c in sorted(analysis["by_operation"].items(), key=lambda x: -x[1]):
            print("   %s: %d 次" % (op, c))

        print("\n[未解决记录]：%d 条" % len(analysis["unresolved"]))

    print("\n[规则改进建议]：")
    if suggestions:
        for i, s in enumerate(suggestions, 1):
            print("\n  [%d] %s" % (i, s))
    else:
        print("   暂无建议。")

    print()


def main():
    records = parse_error_log()
    analysis = analyze_errors(records)
    suggestions = generate_suggestions(analysis)
    print_report(analysis, suggestions)

    if "--save" in sys.argv:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = ERROR_LOG.parent / "规则自检报告_%s.md" % timestamp
        lines = [
            "# 规则自检报告\n",
            "扫描时间：%s\n" % datetime.now().strftime("%Y-%m-%d %H:%M"),
            "总记录数：%d\n" % analysis["total"],
        ]
        if analysis["total"] > 0:
            lines.append("\n## 错误类型分布\n")
            for t, c in sorted(analysis["by_type"].items(), key=lambda x: -x[1]):
                lines.append("- %s: %d 次\n" % (t, c))
        if suggestions:
            lines.append("\n## 改进建议\n")
            for s in suggestions:
                lines.append("- %s\n" % s)
        report_path.write_text("".join(lines), encoding="utf-8")
        print("[FILE] 报告已保存：%s" % report_path)


if __name__ == "__main__":
    main()
