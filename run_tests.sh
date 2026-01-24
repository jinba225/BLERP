#!/bin/bash
# BetterLaser ERP - 测试运行脚本
# 使用方法: ./run_tests.sh [test_type] [options]

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示使用帮助
show_help() {
    cat << EOF
BetterLaser ERP 测试运行脚本

用法:
    ./run_tests.sh [test_type] [options]

测试类型:
    all         - 运行所有测试（默认）
    unit        - 只运行单元测试
    api         - 只运行API测试
    integration - 运行集成测试
    e2e         - 运行端到端测试
    performance - 运行性能测试
    security    - 运行安全测试
    smoke       - 运行烟雾测试
    quick       - 快速测试（跳过慢速测试）
    coverage    - 运行测试并生成覆盖率报告
    app <name>  - 运行特定应用的测试

选项:
    -h, --help     - 显示此帮助信息
    -v, --verbose  - 详细输出
    -p, --parallel - 并行测试
    -f, --failfast - 遇到第一个失败立即停止
    -k <pattern>   - 只运行匹配模式的测试
    --keepdb       - 保持测试数据库（加速）
    --pdb          - 失败时进入调试器

示例:
    ./run_tests.sh                    # 运行所有测试
    ./run_tests.sh unit -p            # 并行运行单元测试
    ./run_tests.sh app sales          # 运行sales应用的测试
    ./run_tests.sh coverage           # 生成覆盖率报告
    ./run_tests.sh quick -k "order"   # 快速测试，只运行包含"order"的测试

EOF
}

# 检查依赖
check_dependencies() {
    print_info "检查测试依赖..."

    if ! command -v pytest &> /dev/null; then
        print_error "pytest未安装，请运行: pip install -r requirements-test.txt"
        exit 1
    fi

    print_success "依赖检查通过"
}

# 创建测试报告目录
create_report_dir() {
    if [ ! -d "test-reports" ]; then
        mkdir -p test-reports
        print_info "创建测试报告目录: test-reports/"
    fi
}

# 运行所有测试
run_all_tests() {
    print_info "运行所有测试..."
    pytest apps/ "$@"
}

# 运行单元测试
run_unit_tests() {
    print_info "运行单元测试..."
    pytest -m "unit or not (integration or api or e2e or performance)" apps/ "$@"
}

# 运行API测试
run_api_tests() {
    print_info "运行API测试..."
    pytest -m "api" apps/ "$@"
}

# 运行集成测试
run_integration_tests() {
    print_info "运行集成测试..."
    pytest -m "integration" apps/ "$@"
}

# 运行E2E测试
run_e2e_tests() {
    print_info "运行端到端测试..."
    pytest -m "e2e" apps/ "$@"
}

# 运行性能测试
run_performance_tests() {
    print_info "运行性能测试..."
    pytest -m "performance" apps/ "$@"
}

# 运行安全测试
run_security_tests() {
    print_info "运行安全测试..."

    # Pytest安全测试
    pytest -m "security" apps/ "$@"

    # Bandit安全扫描
    print_info "运行Bandit安全扫描..."
    bandit -r apps/ -f json -o test-reports/bandit-report.json || true

    # Safety依赖检查
    print_info "运行Safety依赖检查..."
    safety check --json > test-reports/safety-report.json || true

    print_success "安全测试完成，报告保存在 test-reports/"
}

# 运行烟雾测试
run_smoke_tests() {
    print_info "运行烟雾测试..."
    pytest -m "smoke" apps/ "$@"
}

# 快速测试（跳过慢速测试）
run_quick_tests() {
    print_info "运行快速测试（跳过慢速测试）..."
    pytest -m "not slow" apps/ "$@"
}

# 运行特定应用的测试
run_app_tests() {
    local app_name=$1
    shift
    print_info "运行 ${app_name} 应用的测试..."

    if [ ! -d "apps/${app_name}" ]; then
        print_error "应用 ${app_name} 不存在"
        exit 1
    fi

    pytest "apps/${app_name}/" "$@"
}

# 运行测试并生成覆盖率报告
run_coverage() {
    print_info "运行测试并生成覆盖率报告..."

    # 清除旧的覆盖率数据
    coverage erase

    # 运行测试
    pytest apps/ --cov=apps --cov-report=html --cov-report=term-missing --cov-report=xml "$@"

    print_success "覆盖率报告已生成:"
    echo "  - HTML报告: htmlcov/index.html"
    echo "  - XML报告: coverage.xml"
    echo "  - 终端报告: 已显示"

    # 尝试打开HTML报告
    if command -v open &> /dev/null; then
        # macOS
        print_info "正在打开覆盖率报告..."
        open htmlcov/index.html
    elif command -v xdg-open &> /dev/null; then
        # Linux
        print_info "正在打开覆盖率报告..."
        xdg-open htmlcov/index.html
    fi
}

# 清理测试文件
cleanup() {
    print_info "清理测试文件..."

    # 删除pytest缓存
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

    # 删除覆盖率文件
    rm -f .coverage
    rm -f coverage.xml
    rm -rf htmlcov/

    # 删除测试数据库
    rm -f test_db.sqlite3

    print_success "清理完成"
}

# 主函数
main() {
    # 检查帮助
    if [[ "$1" == "-h" || "$1" == "--help" ]]; then
        show_help
        exit 0
    fi

    # 检查清理
    if [[ "$1" == "clean" ]]; then
        cleanup
        exit 0
    fi

    # 检查依赖
    check_dependencies

    # 创建报告目录
    create_report_dir

    # 获取测试类型
    TEST_TYPE="${1:-all}"
    shift || true

    # 记录开始时间
    START_TIME=$(date +%s)

    # 根据测试类型执行
    case "$TEST_TYPE" in
        all)
            run_all_tests "$@"
            ;;
        unit)
            run_unit_tests "$@"
            ;;
        api)
            run_api_tests "$@"
            ;;
        integration)
            run_integration_tests "$@"
            ;;
        e2e)
            run_e2e_tests "$@"
            ;;
        performance)
            run_performance_tests "$@"
            ;;
        security)
            run_security_tests "$@"
            ;;
        smoke)
            run_smoke_tests "$@"
            ;;
        quick)
            run_quick_tests "$@"
            ;;
        coverage)
            run_coverage "$@"
            ;;
        app)
            if [ -z "$1" ]; then
                print_error "请指定应用名称，例如: ./run_tests.sh app sales"
                exit 1
            fi
            run_app_tests "$@"
            ;;
        clean)
            cleanup
            ;;
        *)
            print_error "未知的测试类型: $TEST_TYPE"
            echo ""
            show_help
            exit 1
            ;;
    esac

    # 记录结束时间
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    print_success "测试完成！耗时: ${DURATION}秒"
}

# 运行主函数
main "$@"
