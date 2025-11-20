# Makefile for ToolRegistry Hub Documentation
# 提供构建和测试 MkDocs 文档的便捷命令

.PHONY: help install serve-serve build-serve clean-serve build-all serve-all clean-all clean

# 默认目标
.DEFAULT_GOAL := help

# 颜色定义
RED    = \033[0;31m
GREEN  = \033[0;32m
YELLOW = \033[1;33m
BLUE   = \033[0;34m
NC     = \033[0m # No Color

# 显示帮助信息
help:
	@echo "$(BLUE)ToolRegistry Hub Documentation Makefile$(NC)"
	@echo ""
	@echo "$(YELLOW)安装和依赖管理:$(NC)"
	@echo "  install           - 安装项目依赖"
	@echo ""
	@echo "$(YELLOW)构建和预览:$(NC)"
	@echo "  build-all         - 构建所有语言版本的文档"
	@echo "  serve-all         - 为所有语言版本启动本地服务器"
	@echo "  clean-all         - 清理所有构建文件"
	@echo ""
	@echo "$(YELLOW)英文文档:$(NC)"
	@echo "  build-en          - 构建英文文档"
	@echo "  serve-en          - 启动英文文档本地服务器 (端口 8000)"
	@echo "  clean-en          - 清理英文文档构建文件"
	@echo ""
	@echo "$(YELLOW)中文文档:$(NC)"
	@echo "  build-zh          - 构建中文文档"
	@echo "  serve-zh          - 启动中文文档本地服务器 (端口 8001)"
	@echo "  clean-zh          - 清理中文文档构建文件"
	@echo ""
	@echo "$(YELLOW)其他命令:$(NC)"
	@echo "  clean             - 清理所有构建文件和缓存"
	@echo ""

# 安装依赖
install:
	@echo "$(GREEN)正在安装项目依赖...$(NC)"
	pip install -r requirements.txt

# 构建英文文档
build-en:
	@echo "$(GREEN)正在构建英文文档...$(NC)"
	cd en && mkdocs build
	@echo "$(GREEN)英文文档构建完成！$(NC)"

# 为英文文档启动本地服务器
serve-en:
	@echo "$(GREEN)正在启动英文文档本地服务器...$(NC)"
	@echo "$(BLUE)访问地址: http://localhost:8000$(NC)"
	cd en && mkdocs serve --dev-addr=127.0.0.1:8000

# 清理英文文档构建文件
clean-en:
	@echo "$(GREEN)正在清理英文文档构建文件...$(NC)"
	rm -rf en/site

# 构建中文文档
build-zh:
	@echo "$(GREEN)正在构建中文文档...$(NC)"
	cd zh && mkdocs build
	@echo "$(GREEN)中文文档构建完成！$(NC)"

# 为中文文档启动本地服务器
serve-zh:
	@echo "$(GREEN)正在启动中文文档本地服务器...$(NC)"
	@echo "$(BLUE)访问地址: http://localhost:8001$(NC)"
	cd zh && mkdocs serve --dev-addr=127.0.0.1:8001

# 清理中文文档构建文件
clean-zh:
	@echo "$(GREEN)正在清理中文文档构建文件...$(NC)"
	rm -rf zh/site

# 构建所有语言版本的文档
build-all: build-en build-zh
	@echo "$(GREEN)所有文档版本构建完成！$(NC)"

# 为所有语言版本启动本地服务器（在不同端口）
serve-all:
	@echo "$(GREEN)正在启动所有文档版本的本地服务器...$(NC)"
	@echo "$(BLUE)英文文档: http://localhost:8000$(NC)"
	@echo "$(BLUE)中文文档: http://localhost:8001$(NC)"
	@echo "$(YELLOW)注意: 两个服务器将并行运行，按 Ctrl+C 停止$(NC)"
	@sleep 1
	@$(MAKE) serve-en &
	@sleep 2
	@$(MAKE) serve-zh

# 清理所有构建文件
clean-all: clean-en clean-zh
	@echo "$(GREEN)所有构建文件已清理！$(NC)"

# 清理所有文件（包括缓存）
clean: clean-all
	@echo "$(GREEN)正在清理缓存和临时文件...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -name ".coverage" -type f -delete 2>/dev/null || true
	find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)所有文件已清理！$(NC)"