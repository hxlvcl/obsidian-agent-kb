"""Tests for wiki_audit.py — Wiki 定期体检脚本."""
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import wiki_audit as wa


class TestExtractBody:
    """测试 extract_body — 提取正文（去掉 frontmatter），参数是文件路径"""

    def test_with_frontmatter(self):
        """标准 frontmatter + 正文"""
        with tempfile.TemporaryDirectory() as tmpdir:
            fp = os.path.join(tmpdir, "test.md")
            with open(fp, "w", encoding="utf-8") as f:
                f.write("""---
title: "test"
tags: ["a"]
---

# 标题

正文内容。""")
            result = wa.extract_body(fp)
            assert "# 标题" in result
            assert "正文内容" in result
            assert "title" not in result

    def test_no_frontmatter(self):
        """无 frontmatter 时返回全部内容"""
        with tempfile.TemporaryDirectory() as tmpdir:
            fp = os.path.join(tmpdir, "test.md")
            with open(fp, "w", encoding="utf-8") as f:
                f.write("# 直接标题\n\n正文内容。")
            result = wa.extract_body(fp)
            assert "# 直接标题" in result
            assert "正文内容" in result

    def test_dashed_content_not_frontmatter(self):
        """内容中有 --- 但不是 frontmatter 标记"""
        with tempfile.TemporaryDirectory() as tmpdir:
            fp = os.path.join(tmpdir, "test.md")
            with open(fp, "w", encoding="utf-8") as f:
                f.write("# 标题\n\n---\n\n正文内容。")
            result = wa.extract_body(fp)
            assert "# 标题" in result
            assert "---" in result


class TestExtractAllLinks:
    """测试 extract_all_links — 提取 [[链接]]"""

    def test_simple_links(self):
        """简单 [[链接]]"""
        text = "参见 [[文章A]] 和 [[文章B]]"
        links = wa.extract_all_links(text)
        assert "文章A" in links
        assert "文章B" in links

    def test_links_with_anchor(self):
        """带 #锚点 的链接"""
        text = "[[文章#章节名]]"
        links = wa.extract_all_links(text)
        assert "文章" in links
        assert "章节名" not in links

    def test_links_with_alias(self):
        """带 |别名 的链接"""
        text = "[[长文件名|短名]]"
        links = wa.extract_all_links(text)
        assert "长文件名" in links
        assert "短名" not in links

    def test_multiple_links_in_line(self):
        """一行多个链接"""
        text = "[[A]] [[B]] [[C]]"
        links = wa.extract_all_links(text)
        assert len(links) == 3
        assert links == ["A", "B", "C"]

    def test_no_links(self):
        """无链接的文本"""
        text = "纯文本，没有链接。"
        links = wa.extract_all_links(text)
        assert links == []

    def test_links_with_alias_and_anchor(self):
        """同时有别名和锚点"""
        text = "[[文章名#节1|显示名]]"
        links = wa.extract_all_links(text)
        assert "文章名" in links
        assert "节1" not in links
        assert "显示名" not in links


class TestCheckEmptyPages:
    """测试 check_empty_pages — 空洞页检测;
       注意：脚本硬编码了 WIKI_DIR，测试直接调函数传文件路径"""

    def test_empty_page_detected(self):
        """内容过少被检测为空洞页"""
        with tempfile.TemporaryDirectory() as tmpdir:
            fp = os.path.join(tmpdir, "空洞页.md")
            with open(fp, "w", encoding="utf-8") as f:
                f.write("---\ntitle: test\n---\n\n# 标题\n\n内容很少。")
            # 临时 mock WIKI_DIR 避免 D: 冲突
            old_dir = wa.WIKI_DIR
            wa.WIKI_DIR = tmpdir
            try:
                results = wa.check_empty_pages([fp])
                assert len(results) == 1
            finally:
                wa.WIKI_DIR = old_dir

    def test_normal_page_not_flagged(self):
        """正常内容不被标记"""
        with tempfile.TemporaryDirectory() as tmpdir:
            fp = os.path.join(tmpdir, "正常页.md")
            with open(fp, "w", encoding="utf-8") as f:
                f.write("# 标题\n\n" + "正文内容。" * 50)
            old_dir = wa.WIKI_DIR
            wa.WIKI_DIR = tmpdir
            try:
                results = wa.check_empty_pages([fp])
                assert len(results) == 0
            finally:
                wa.WIKI_DIR = old_dir
