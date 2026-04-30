"""Tests for safe_link_appender.py — 知识库链接安全追加脚本."""
import os
import sys
import tempfile
import pytest

# Add scripts dir to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import safe_link_appender as sla


class TestResolveFilename:
    """测试 resolve_filename — 短名→完整文件名解析"""

    def test_exact_match(self):
        """精确匹配：文件名完全正确时直接返回"""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "00-收件箱"), exist_ok=True)
            path = os.path.join(tmpdir, "00-收件箱", "测试文章.md")
            with open(path, "w", encoding="utf-8") as f:
                f.write("# test")
            result = sla.resolve_filename("测试文章", tmpdir)
            assert result == "测试文章"

    def test_prefix_match_longest_wins(self):
        """前缀匹配：无精确匹配时最长前缀胜出"""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "00-收件箱"), exist_ok=True)
            for name in ["A_longer", "A_longest"]:
                with open(os.path.join(tmpdir, "00-收件箱", f"{name}.md"), "w") as f:
                    f.write("# test")
            result = sla.resolve_filename("A_lon", tmpdir)
            assert result == "A_longest"  # 无精确匹配，最长前缀胜出

    def test_no_match_returns_original(self):
        """无匹配时返回原值"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = sla.resolve_filename("不存在的文件", tmpdir)
            assert result == "不存在的文件"

    def test_empty_input(self):
        """空输入直接返回"""
        result = sla.resolve_filename("", "/tmp")
        assert result == ""


class TestIsAllowed:
    """测试 is_allowed — 白名单/黑名单检查"""

    def test_allowed_inbox(self):
        """00-收件箱在白名单"""
        path = os.path.join(sla.VAULT, "00-收件箱", "test.md")
        ok, err = sla.is_allowed(path)
        assert ok
        assert err == ""

    def test_allowed_wiki(self):
        """02-Wiki 在白名单"""
        path = os.path.join(sla.VAULT, "02-Wiki", "01-科技", "test.md")
        ok, err = sla.is_allowed(path)
        assert ok
        assert err == ""

    def test_blocked_sucai(self):
        """01-素材库在黑名单"""
        path = os.path.join(sla.VAULT, "01-素材库", "教程", "test.md")
        ok, err = sla.is_allowed(path)
        assert not ok
        assert "BLOCKED" in err
        assert "01-素材库" in err

    def test_blocked_system(self):
        """06-系统在黑名单"""
        path = os.path.join(sla.VAULT, "06-系统", "模板", "test.md")
        ok, err = sla.is_allowed(path)
        assert not ok
        assert "BLOCKED" in err

    def test_blocked_thinking(self):
        """03-思考在黑名单"""
        path = os.path.join(sla.VAULT, "03-思考", "test.md")
        ok, err = sla.is_allowed(path)
        assert not ok

    def test_blocked_project(self):
        """04-项目在黑名单"""
        path = os.path.join(sla.VAULT, "04-项目", "test.md")
        ok, err = sla.is_allowed(path)
        assert not ok

    def test_blocked_output(self):
        """05-产出在黑名单"""
        path = os.path.join(sla.VAULT, "05-产出", "test.md")
        ok, err = sla.is_allowed(path)
        assert not ok

    def test_not_in_any_list(self):
        """不在任何列表中的路径也被拒绝"""
        path = os.path.join(sla.VAULT, "99-不存在", "test.md")
        ok, err = sla.is_allowed(path)
        assert not ok
        assert "不在白名单目录" in err


class TestIsWikiConcept:
    """测试 _is_wiki_concept — Wiki 概念页判断"""

    def test_is_wiki_concept(self):
        """02-Wiki 下的文件被识别为概念页"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 临时替换 VAULT
            old_vault = sla.VAULT
            sla.VAULT = tmpdir
            os.makedirs(os.path.join(tmpdir, "02-Wiki", "01-科技"), exist_ok=True)
            with open(os.path.join(tmpdir, "02-Wiki", "01-科技", "Skill生态.md"), "w") as f:
                f.write("# test")
            try:
                assert sla._is_wiki_concept("Skill生态")
            finally:
                sla.VAULT = old_vault

    def test_not_wiki_concept(self):
        """非 Wiki 文件不被识别"""
        with tempfile.TemporaryDirectory() as tmpdir:
            old_vault = sla.VAULT
            sla.VAULT = tmpdir
            os.makedirs(os.path.join(tmpdir, "01-素材库"), exist_ok=True)
            with open(os.path.join(tmpdir, "01-素材库", "普通文章.md"), "w") as f:
                f.write("# test")
            try:
                assert not sla._is_wiki_concept("普通文章")
            finally:
                sla.VAULT = old_vault
