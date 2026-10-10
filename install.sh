#!/bin/bash
# 一键安装：把 chatlog-output skill 复制到 Codex 的 skills 目录（已存在则先备份）
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
DEST="${CODEX_HOME:-$HOME/.codex}/skills/chatlog-output"
command -v python3 >/dev/null || { echo "缺少依赖: python3"; exit 1; }
mkdir -p "$(dirname "$DEST")"
if [ -e "$DEST" ]; then mv "$DEST" "$DEST.bak.$(date +%Y%m%d%H%M%S)"; echo "已备份原有版本"; fi
cp -R "$HERE/chatlog-output" "$DEST"
echo "已安装到 ${DEST}。重启 Codex 后即可使用（例如说：用 \$chatlog-output 导出当前会话）。"
