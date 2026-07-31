#!/usr/bin/env python3
"""批量重命名工具 renamer — 纯标准库实现，零第三方依赖

功能：
  - 前缀 / 后缀添加
  - 文本替换
  - 扩展名修改
  - 顺序编号（自然排序）
  - 支持递归子目录
  - 干跑预览 + 确认，防误操作

两种使用方式：
  1. 交互模式：直接双击运行 exe，按提示操作
  2. 命令行模式：
     renamer --dir "D:\\下载" --prefix "2024_"
     renamer --dir . --replace "旧" "新" --dry-run
     renamer --dir . --number --start 1 --digits 3
"""

import argparse
import re
import sys
from pathlib import Path

VERSION = "1.0.0"


# ---------- 工具函数 ----------

def natural_key(name: str):
    """自然排序键：'2' 排在 '10' 前面"""
    return [int(t) if t.isdigit() else t.lower()
            for t in re.split(r"(\d+)", name)]


def pause() -> None:
    """等待回车（管道输入结束时不报错）"""
    try:
        input("按回车退出...")
    except EOFError:
        pass


def safe_print(text: str) -> None:
    """兼容 Windows 旧控制台的打印"""
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    print(text)


def collect_files(root: Path, recursive: bool, include_hidden: bool) -> list:
    """收集目标文件（排除目录、默认跳过隐藏文件）"""
    pattern = "**/*" if recursive else "*"
    files = []
    for p in root.glob(pattern):
        if not p.is_file():
            continue
        if not include_hidden and p.name.startswith("."):
            continue
        files.append(p)
    return sorted(files, key=lambda p: natural_key(p.name))


def build_new_name(p: Path, args) -> tuple:
    """按规则计算新文件名，返回 (新名, 变化描述)；无变化返回 (None, None)"""
    stem, suffix = p.stem, p.suffix
    old_name = p.name
    new_stem = stem

    if args.replace:
        old_txt, new_txt = args.replace
        if old_txt in new_stem:
            new_stem = new_stem.replace(old_txt, new_txt)
    if args.prefix:
        new_stem = args.prefix + new_stem
    if args.suffix:
        new_stem = new_stem + args.suffix
    if args.ext:
        suffix = args.ext if args.ext.startswith(".") else "." + args.ext

    new_name = new_stem + suffix
    if new_name == old_name:
        return None, None
    return new_name, f"{old_name}  ->  {new_name}"


def apply_rename(root: Path, files: list, args, counter) -> dict:
    """执行重命名，返回统计信息"""
    stats = {"renamed": 0, "skipped_exists": 0, "skipped_same": 0, "failed": 0}
    for i, p in enumerate(files, start=1):
        # 先应用其他规则，再统一叠加编号（编号始终生效）
        new_name, desc = build_new_name(p, args)
        if args.number:
            num = f"{args.start + i - 1:0{args.digits}d}"
            base = new_name if new_name is not None else p.name
            new_name = f"{num}_{base}"
        elif new_name is None:
            stats["skipped_same"] += 1
            continue

        target = p.with_name(new_name)
        if target.exists():
            safe_print(f"[跳过-已存在] {p.name}  ->  {new_name}")
            stats["skipped_exists"] += 1
            continue

        safe_print(f"  {p.name}  ->  {new_name}")
        if args.dry_run:
            counter[0] += 1
            continue
        try:
            p.rename(target)
            stats["renamed"] += 1
        except OSError as e:
            safe_print(f"[失败] {p.name}: {e}")
            stats["failed"] += 1
    return stats


# ---------- 交互模式 ----------

def interactive() -> None:
    safe_print("=" * 52)
    safe_print("  批量重命名工具 v" + VERSION + "（纯 Python 实现）")
    safe_print("=" * 52)
    root = input("目标目录（直接回车 = 当前目录）: ").strip()
    root = Path(root) if root else Path.cwd()
    if not root.is_dir():
        safe_print(f"[错误] 目录不存在: {root}")
        pause()
        return

    safe_print("\n目录中的文件：")
    files = collect_files(root, recursive=False, include_hidden=False)
    if not files:
        safe_print("（空目录，没有可重命名的文件）")
        pause()
        return
    for i, f in enumerate(files, 1):
        safe_print(f"  {i:3d}. {f.name}")
    safe_print(f"共 {len(files)} 个文件")

    safe_print("\n请选择操作（可多选，用逗号分隔，如 1,3）：")
    safe_print("  1. 添加前缀    2. 添加后缀")
    safe_print("  3. 文本替换    4. 修改扩展名")
    safe_print("  5. 顺序编号（自动加在最前面，如 01_xxx）")
    choice = input("选择: ").strip()
    choices = [int(c) for c in re.findall(r"\d", choice) if int(c) in range(1, 6)]

    # 构造与命令行一致的 args 对象
    ns = argparse.Namespace(
        prefix="", suffix="", replace=None, ext="", number=False,
        start=1, digits=2, dry_run=False, yes=False,
        recursive=False, include_hidden=False,
    )
    if 1 in choices:
        ns.prefix = input("前缀内容: ").strip()
    if 2 in choices:
        ns.suffix = input("后缀内容: ").strip()
    if 3 in choices:
        old_t = input("要被替换的文本: ")
        new_t = input("替换为（留空=删除）: ")
        if old_t:
            ns.replace = (old_t, new_t)
    if 4 in choices:
        ns.ext = input("新扩展名（如 txt，留空跳过）: ").strip()
    if 5 in choices:
        ns.number = True
        try:
            ns.start = int(input(f"起始编号（默认 {ns.start}）: ").strip() or ns.start)
            ns.digits = int(input(f"编号位数（默认 {ns.digits}）: ").strip() or ns.digits)
        except ValueError:
            pass

    if not any([ns.prefix, ns.suffix, ns.replace, ns.ext, ns.number]):
        safe_print("未选择任何操作，退出。")
        return

    # 预览（严格干跑，绝不真改）
    safe_print("\n【预览】将执行以下重命名：")
    preview_ns = argparse.Namespace(**vars(ns))
    preview_ns.dry_run = True
    counter = [0]
    apply_rename(root, files, preview_ns, counter)
    safe_print(f"\n预览共 {counter[0]} 处变更")
    if counter[0] == 0:
        safe_print("没有需要重命名的文件。")
        pause()
        return
    confirm = input("确认执行？（y/n）: ").strip().lower()
    if confirm not in ("y", "yes", "是", "确认"):
        safe_print("已取消。")
        pause()
        return

    safe_print("\n执行中...")
    files2 = collect_files(root, recursive=False, include_hidden=False)
    stats = apply_rename(root, files2, ns, counter)
    safe_print(f"\n完成：成功重命名 {stats['renamed']} 个，"
               f"跳过已存在 {stats['skipped_exists']} 个，失败 {stats['failed']} 个")
    pause()


# ---------- 命令行模式 ----------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="renamer",
        description="批量重命名工具（纯标准库，无第三方依赖）",
        epilog="示例：\n"
               "  renamer --dir D:/下载 --prefix 2024_\n"
               "  renamer --dir . --replace 旧 新 --dry-run\n"
               "  renamer --dir . --number --start 1 --digits 3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--dir", default=".", help="目标目录（默认当前目录）")
    p.add_argument("--prefix", default="", help="添加前缀")
    p.add_argument("--suffix", default="", help="添加后缀")
    p.add_argument("--replace", nargs=2, metavar=("OLD", "NEW"), help="文本替换")
    p.add_argument("--ext", default="", help="修改扩展名（如 txt）")
    p.add_argument("--number", action="store_true", help="添加顺序编号前缀")
    p.add_argument("--start", type=int, default=1, help="编号起始值（默认 1）")
    p.add_argument("--digits", type=int, default=2, help="编号位数（默认 2）")
    p.add_argument("--recursive", action="store_true", help="递归子目录")
    p.add_argument("--include-hidden", action="store_true", help="包含隐藏文件")
    p.add_argument("--dry-run", action="store_true", help="仅预览，不执行")
    p.add_argument("--yes", action="store_true", help="跳过确认")
    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    has_rule = any([args.prefix, args.suffix, args.replace, args.ext, args.number])
    if not has_rule:
        interactive()
        return 0

    root = Path(args.dir)
    if not root.is_dir():
        safe_print(f"[错误] 目录不存在: {root}")
        return 1

    files = collect_files(root, args.recursive, args.include_hidden)
    if not files:
        safe_print("没有可重命名的文件。")
        return 0

    counter = [0]
    if not args.yes:
        safe_print(f"共 {len(files)} 个文件，预览如下：")
        apply_rename(root, files, args, counter)
        if counter[0] == 0:
            safe_print("没有需要重命名的文件。")
            return 0
        confirm = input(f"确认执行这 {counter[0]} 处变更？（y/n）: ").strip().lower()
        if confirm not in ("y", "yes", "是", "确认"):
            safe_print("已取消。")
            return 0

    stats = apply_rename(root, files, args, counter)
    safe_print(f"\n完成：成功 {stats['renamed']} 个，已存在跳过 {stats['skipped_exists']} 个，失败 {stats['failed']} 个")
    return 0


if __name__ == "__main__":
    sys.exit(main())
