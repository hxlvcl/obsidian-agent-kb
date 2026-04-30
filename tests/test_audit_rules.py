"""Tests for audit_rules.py — 规则自检脚本."""
import os
import sys
import tempfile
from pathlib import Path
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import audit_rules as ar


class TestParseErrorLog:
    """测试 parse_error_log — 解析错误日志（markdown 格式）"""

    def test_parse_basic_entry(self):
        """解析基本错误记录"""
        content = """## 2026-04-29

### 入库自检失败

**错误**：frontmatter 缺少闭合 ---
**文件**：00-收件箱/某文章.md
**原因**：清理残留时误删了第二个 ---
**状态**：已修复"""

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "错误日志.md")
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(content)

            # Mock VAULT_DIR
            old_path = ar.VAULT_DIR
            old_log = ar.ERROR_LOG
            ar.VAULT_DIR = Path(tmpdir)
            ar.ERROR_LOG = Path(log_path)
            try:
                records = ar.parse_error_log()
                assert len(records) == 1
                r = records[0]
                assert r["_heading"] == "入库自检失败"
                assert r["错误"] == "frontmatter 缺少闭合 ---"
                assert r["文件"] == "00-收件箱/某文章.md"
                assert r["状态"] == "已修复"
            finally:
                ar.VAULT_DIR = old_path
                ar.ERROR_LOG = old_log

    def test_parse_multiple_entries(self):
        """解析多条记录"""
        content = """## 2026-04-29

### 错误1

**类型**：语法错误
**状态**：已修复

### 错误2

**类型**：权限错误
**状态**：未解决"""

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "错误日志.md")
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(content)

            old_path = ar.VAULT_DIR
            old_log = ar.ERROR_LOG
            ar.VAULT_DIR = Path(tmpdir)
            ar.ERROR_LOG = Path(log_path)
            try:
                records = ar.parse_error_log()
                assert len(records) == 2
                assert records[0]["_heading"] == "错误1"
                assert records[1]["_heading"] == "错误2"
                assert records[0]["状态"] == "已修复"
                assert records[1]["状态"] == "未解决"
            finally:
                ar.VAULT_DIR = old_path
                ar.ERROR_LOG = old_log

    def test_skips_code_blocks(self):
        """跳过代码块中的示例（不会被解析为记录）"""
        content = """## 2026-04-29

```markdown
### 这是示例不是真实记录
**类型**：示例
```

### 真实记录

**类型**：真实
**状态**：已修复"""

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "错误日志.md")
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(content)

            old_path = ar.VAULT_DIR
            old_log = ar.ERROR_LOG
            ar.VAULT_DIR = Path(tmpdir)
            ar.ERROR_LOG = Path(log_path)
            try:
                records = ar.parse_error_log()
                assert len(records) == 1
                assert records[0]["_heading"] == "真实记录"
            finally:
                ar.VAULT_DIR = old_path
                ar.ERROR_LOG = old_log


class TestAnalyzeErrors:
    """测试 analyze_errors — 聚类分析"""

    def test_empty_records(self):
        """空记录"""
        result = ar.analyze_errors([])
        assert result["total"] == 0
        assert result["by_type"] == {}
        assert result["unresolved"] == []

    def test_single_record(self):
        """单条记录"""
        records = [{"_heading": "入库自检失败", "操作": "入库", "状态": "已修复"}]
        result = ar.analyze_errors(records)
        assert result["total"] == 1
        assert result["by_type"]["入库自检失败"] == 1
        assert result["by_operation"]["入库"] == 1
        assert len(result["unresolved"]) == 0

    def test_unresolved_detected(self):
        """检测未解决的错误"""
        records = [
            {"_heading": "入库自检失败", "状态": "未解决"},
            {"_heading": "脚本错误", "状态": "已修复"},
            {"_heading": "权限错误", "状态": ""},  # 空状态也视为未解决
        ]
        result = ar.analyze_errors(records)
        assert result["total"] == 3
        assert len(result["unresolved"]) == 2

    def test_group_by_type(self):
        """按类型分组计数"""
        records = [
            {"_heading": "入库自检失败", "状态": "已修复"},
            {"_heading": "入库自检失败", "状态": "已修复"},
            {"_heading": "脚本错误", "状态": "已修复"},
        ]
        result = ar.analyze_errors(records)
        assert result["by_type"]["入库自检失败"] == 2
        assert result["by_type"]["脚本错误"] == 1
