# chatlog-output：把 Codex 会话导出成 Markdown

整理日期：2026-10-10。这是我本机 Codex 里的 `chatlog-output` skill，原样复制自 `~/.codex/skills/chatlog-output/`。

## 它做什么

Codex 会把每次会话存成 JSONL 文件，放在 `~/.codex/sessions/` 下。这个 skill 把这种文件转成可读的 Markdown，内容包括：

- 用户和 Codex 的对话
- 默认还有工具调用和工具输出（输出超过 5000 字符会截断），读起来像一份操作日志

导出的文件名形如 `2026-09-29-231507-codex-chatlog-<目录名>.md`。

## 文件

| 文件 | 作用 |
|---|---|
| `chatlog-output/SKILL.md` | 给 Codex 看的使用说明 |
| `chatlog-output/scripts/export_codex_chatlog.py` | 干活的脚本，只用 Python 标准库，没有第三方依赖 |
| `chatlog-output/agents/openai.yaml` | Codex 界面里显示的名字和默认提示语 |
| `chatlog-output/tests/test_export_codex_chatlog.py` | 单元测试 |
| `install.sh` | 一键安装 |

## 安装

只需要 `python3`。

```bash
bash install.sh
```

装到 `~/.codex/skills/chatlog-output/`。设置了 `CODEX_HOME` 的话，就装到 `$CODEX_HOME/skills/` 下。原来已经有同名文件夹的话，会先备份。装好后重启 Codex。

## 使用

**在 Codex 里**：直接说"用 `$chatlog-output` 导出当前会话"。Codex 会先问你导出到哪个文件夹。

**在终端里**：

```bash
S=~/.codex/skills/chatlog-output/scripts/export_codex_chatlog.py

# 列出当前目录下最近的会话；带 * 的是最新一条
python3 $S list --cwd "$PWD" --limit 5

# 导出指定会话
python3 $S export --session-id "<会话id>" --output-dir "<输出文件夹>" --include-tools --verbose
```

常用参数：

| 参数 | 作用 |
|---|---|
| 不加 `--include-tools` | 只导出对话 |
| `--include-system` | 连系统和开发者指令一起导出 |
| `--max-output-chars N` | 调整工具输出的截断长度，0 表示不截断 |
| `--sessions-root <路径>` | 读非默认位置或归档的会话目录 |

运行测试：`cd chatlog-output && python3 -m unittest discover -s tests`

## 注意

导出的 Markdown 会原样包含会话内容和本机路径，包括工作目录和源文件路径。分享导出结果前，先自己检查一遍。
