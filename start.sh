#!/bin/bash
# Django ERP 启动脚本（快捷方式）
# 真正的脚本位于 scripts/start_server.sh

cd "$(dirname "$0")"
./scripts/start_server.sh "$@"
