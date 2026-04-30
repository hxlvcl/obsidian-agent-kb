"""Tests for supplement_linker.py — 补充观点链接插入脚本."""
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import supplement_linker as sl


class TestResolveArticle:
    """测试 resolve_article — 短名→完整文件名"""

    def test_exact_match(self):
        """精确匹配"""
        name_index = {"测试文章.md": "测试文章.md", "其他.md": "其他.md"}
        result = sl.resolve_article("测试文章", name_index)
        assert result == "测试文章"

    def test_prefix_match(self):
        """前缀匹配 — 无精确匹配时最长胜出"""
        # resolve_article 先精确匹配（partial + .md），要确保没有精确命中才走前缀
        name_index = {
            "测试补全A.md": "测试补全A.md",
            "测试补全AB.md": "测试补全AB.md",
        }
        # "测试补全" + ".md" = "测试补全.md" 不在索引 → 走前缀匹配
        result = sl.resolve_article("测试补全", name_index)
        assert result == "测试补全AB"  # 最长前缀

    def test_no_match(self):
        """无匹配返回 None"""
        name_index = {"完全无关.md": "完全无关.md"}
        result = sl.resolve_article("测试", name_index)
        assert result is None

    def test_empty_index(self):
        """空索引"""
        result = sl.resolve_article("测试", {})
        assert result is None


class TestScanWikiFiles:
    """测试 scan_wiki_files — 扫描 Wiki 目录"""

    def test_scan_excludes_index(self):
        """排除 _index.md"""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "01-科技"), exist_ok=True)
            with open(os.path.join(tmpdir, "01-科技", "概念A.md"), "w") as f:
                f.write("# A")
            with open(os.path.join(tmpdir, "_index.md"), "w") as f:
                f.write("# index")

            files = sl.scan_wiki_files(tmpdir)
            assert len(files) == 1
            assert "概念A.md" in files[0]
            assert "_index.md" not in "\n".join(files)

    def test_empty_directory(self):
        """空目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            files = sl.scan_wiki_files(tmpdir)
            assert files == []
