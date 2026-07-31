# win-exe-builder

在树莓派上开发 Python，通过 GitHub Actions 自动打包 Windows 10 EXE。

## 工作流程

1. 本地修改 `main.py`（或换成自己的入口脚本）和 `requirements.txt`
2. `git push` 到 GitHub（走 SSH 443，无需翻墙）
3. GitHub Actions 自动在 Windows 构建机上运行 PyInstaller
4. 下载产物：

```bash
gh run download --repo <用户名>/<仓库名> -n windows-exe -D dist
```

## 自定义

- 入口脚本名：修改 `.github/workflows/build-exe.yml` 中 `pyinstaller --name myapp ... main.py`
- 生成的 exe 名称：`--name` 参数
- 无控制台窗口（GUI 程序）：加 `--windowed` 参数
