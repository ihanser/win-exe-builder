# 批量重命名工具 renamer（纯标准库，零第三方依赖）

在树莓派上开发，通过 GitHub Actions 自动打包成 Windows 10 EXE。

## 功能

- 添加前缀 / 后缀
- 文本替换
- 修改扩展名
- 顺序编号（自然排序，`photo_2` 排在 `photo_10` 前）
- 递归子目录、隐藏文件选项
- 干跑预览 + 确认，防误操作
- 交互模式（双击 exe）与命令行模式双支持

## 用法（Windows 命令行）

```bat
renamer.exe --dir "D:\下载" --prefix "2024_"
renamer.exe --dir . --replace "旧" "新" --dry-run
renamer.exe --dir . --number --start 1 --digits 3
renamer.exe --dir D:\照片 --ext jpg
```

双击 exe 进入交互模式，按提示操作。

## 关于依赖

脚本**仅使用 Python 标准库**（os/pathlib/re/argparse），无任何第三方包。
PyInstaller 打包时自动把 Python 运行时和标准库全部打进单个 exe，
因此**依赖已完整包含**，目标 Windows 机器无需安装 Python。

若以后脚本引入第三方库，只需在 `requirements.txt` 声明，构建时自动 `pip install` 一并打包。

## 重新打包

```bash
git add . && git commit -m "更新" && git push
gh run download -n windows-exe -D dist   # 等待构建完成后执行
```

## 构建

`.github/workflows/build-exe.yml`：windows-latest + PyInstaller `--onefile`
