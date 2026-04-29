#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
git_control.py — AI 自驱 Git 版本控制脚本

三环方案的第三环：在每次操作前后自动创建 Git 快照，
实现可追溯、可回滚的版本控制。

使用方式（由 AI 在任务前/后调用）：
    python git_control.py pre "入库整理"
    python git_control.py post "入库整理：移动5篇到素材库"
    python git_control.py restore "01-素材库/教程/xxx.md"
    python git_control.py rollback
    python git_control.py status

权限分区：
  - 活动区（00-收件箱/）：AI 可自由创建/修改/移动
  - 只读区（01-素材库/）：AI 只读，仅可建立双向链接
  - 禁止区（05-系统/）：AI 禁止修改，除非用户明确允许
"""

import os
import sys
import subprocess
import datetime

VAULT_PATH = r"{{VAULT_PATH}}"


def _safe_print(text):
    """安全打印，过滤掉 GBK 不支持的字符。"""
    try:
        print(text)
    except UnicodeEncodeError:
        # 替换掉 emoji 等无法在 GBK 中显示的字符
        safe = text.encode("gbk", errors="replace").decode("gbk", errors="replace")
        print(safe)


def _git(*args, capture=True):
    """执行 Git 命令并返回结果。"""
    cmd = ["git", "-C", VAULT_PATH] + list(args)
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            encoding="utf-8",
            timeout=30,
        )
        return result
    except subprocess.TimeoutExpired:
        return None
    except Exception as e:
        return None


def commit_before_work(action="未指定操作"):
    """任务前快照：提交当前状态，便于任务出错后回滚。"""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    message = f"🔄 [pre] before {action} @ {timestamp}"

    # 先检查是否有未跟踪或修改的文件
    status_result = _git("status", "--porcelain")
    if not status_result or not status_result.stdout.strip():
        # 工作区干净，依然创建空提交作为标记 rollback 锚点
        result = _git("commit", "--allow-empty", "-m", message)
        if result and result.returncode == 0:
            commit_hash = _git("rev-parse", "--short", "HEAD")
            sha = commit_hash.stdout.strip() if commit_hash else "未知"
            return {"success": True, "message": f"工作区干净，已创建空快照标记: {sha}", "commit": sha}
        else:
            return {"success": False, "message": f"空提交失败: {result.stderr if result else '超时'}"}

    result = _git("add", "-A")
    if result and result.returncode != 0:
        return {"success": False, "message": f"git add 失败: {result.stderr}"}

    result = _git("commit", "-m", message, "--allow-empty")
    if result and result.returncode == 0:
        commit_hash = _git("rev-parse", "--short", "HEAD")
        sha = commit_hash.stdout.strip() if commit_hash else "未知"
        return {"success": True, "message": f"快照已创建: {sha}", "commit": sha}
    else:
        return {"success": False, "message": f"commit 失败: {result.stderr if result else '超时'}"}


def commit_after_work(message="未记录"):
    """任务后提交：记录本次操作的变更。"""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    full_message = f"📝 [post] {message} @ {timestamp}"

    status_result = _git("status", "--porcelain")
    if not status_result or not status_result.stdout.strip():
        return {"success": True, "message": "无变更，跳过提交", "commit": None}

    result = _git("add", "-A")
    if result and result.returncode != 0:
        return {"success": False, "message": f"git add 失败: {result.stderr}"}

    result = _git("commit", "-m", full_message)
    if result and result.returncode == 0:
        commit_hash = _git("rev-parse", "--short", "HEAD")
        sha = commit_hash.stdout.strip() if commit_hash else "未知"
        return {"success": True, "message": f"变更已提交: {sha}", "commit": sha}
    else:
        return {"success": False, "message": f"commit 失败: {result.stderr if result else '超时'}"}


def restore_file(file_path):
    """恢复单个文件到最近的 commit 状态。"""
    full_path = os.path.join(VAULT_PATH, file_path)
    if not os.path.exists(full_path):
        return {"success": False, "message": f"文件不存在: {file_path}"}

    result = _git("checkout", "--", file_path)
    if result and result.returncode == 0:
        return {"success": True, "message": f"已恢复: {file_path}"}
    else:
        return {"success": False, "message": f"恢复失败: {result.stderr if result else '超时'}"}


def rollback_to_commit(commit_hash=None):
    """回滚到指定 commit，丢弃之后的所有改动。"""
    if commit_hash:
        target = commit_hash
    else:
        target = "HEAD~1"  # 默认回滚到上一次 commit（撤销本次 pre 之后的所有操作）
    # 硬重置到目标 commit，丢弃工作区和暂存区的所有变更
    result = _git("reset", "--hard", target)
    if result and result.returncode == 0:
        return {"success": True, "message": f"已回滚到 {target}，所有改动已丢弃"}
    else:
        return {"success": False, "message": f"回滚失败: {result.stderr if result else '超时'}"}


def show_status():
    """显示当前 Git 状态和最近提交。"""
    status = _git("status", "--short")
    status_text = status.stdout.strip() if status and status.stdout else "（干净）"

    log = _git("log", "--oneline", "-5")
    log_text = log.stdout.strip() if log and log.stdout else "（无提交）"

    return {
        "status": status_text,
        "recent_commits": log_text,
    }


def show_diff(files=None):
    """显示未暂存的差异。"""
    if files:
        result = _git("diff", "--", *files)
    else:
        result = _git("diff")
    return result.stdout if result and result.stdout else "（无差异）"


# ========== CLI 入口 ==========

HELP_TEXT = """
用法:
  python git_control.py pre <操作描述>      # 任务前快照
  python git_control.py post <操作描述>     # 任务后提交
  python git_control.py restore <文件路径>  # 恢复单个文件
  python git_control.py rollback [commit]   # 回滚到指定/上个commit
  python git_control.py status              # 查看状态
  python git_control.py diff [文件]         # 查看差异
"""

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(HELP_TEXT)
        sys.exit(0)

    command = sys.argv[1]

    if command == "pre":
        action = " ".join(sys.argv[2:]) or "未命名操作"
        result = commit_before_work(action)
        print(result["message"])
        sys.exit(0 if result["success"] else 1)

    elif command == "post":
        message = " ".join(sys.argv[2:]) or "未记录"
        result = commit_after_work(message)
        print(result["message"])
        sys.exit(0 if result["success"] else 1)

    elif command == "restore":
        if len(sys.argv) < 3:
            print("用法: python git_control.py restore <文件路径>")
            sys.exit(1)
        file_path = sys.argv[2]
        result = restore_file(file_path)
        print(result["message"])
        sys.exit(0 if result["success"] else 1)

    elif command == "rollback":
        commit = sys.argv[2] if len(sys.argv) > 2 else None
        result = rollback_to_commit(commit)
        print(result["message"])
        sys.exit(0 if result["success"] else 1)

    elif command == "status":
        info = show_status()
        _safe_print("=== 工作区状态 ===")
        _safe_print(info["status"])
        _safe_print("\n=== 最近提交 ===")
        _safe_print(info["recent_commits"])

    elif command == "diff":
        files = sys.argv[2:] if len(sys.argv) > 2 else None
        print(show_diff(files))

    else:
        print(f"未知命令: {command}")
        print(HELP_TEXT)
        sys.exit(1)
