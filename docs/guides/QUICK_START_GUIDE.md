# Django ERP 快速启动指南 🚀

**适用对象**: 开发者、运维人员
**环境**: 开发 / 生产
**最后更新**: 2026-02-08

---

## 🎯 5分钟快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
python --version  # 应显示 Python 3.13+
```

### 2. 配置环境变量
```bash
cp .env.example .env
nano .env

# 最小配置
DEBUG=True
SECRET_KEY=your-secret-key-here
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
```

### 3. 初始化数据库
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. 启动开发服务器
```bash
python manage.py runserver
# 访问: http://localhost:8000
```

### 5. 运行测试
```bash
pytest apps/**/test_e2e_*.py -v
# 应该看到: 18 passed
```

---

## 🛠️ 开发工具

### 代码质量检查
```bash
# Black格式化
black . --line-length=100

# flake8检查
flake8 . --max-line-length=100

# isort排序
isort . --profile black

# Pre-commit hooks
pre-commit run --all-files
```

### 测试工具
```bash
# E2E测试
pytest apps/**/test_e2e_*.py -v

# 覆盖率报告
pytest apps/**/test_e2e_*.py --cov=apps --cov-report=html
open htmlcov/index.html
```

---

## 💾 数据库备份

### 备份数据库
```bash
# SQLite（开发环境）
./scripts/backup.sh development

# PostgreSQL（生产环境）
./scripts/backup.sh production

# 查看备份
ls -lh backups/
```

### 定时备份
```bash
cp scripts/crontab.example /tmp/my-crontab
nano /tmp/my-crontab  # 修改PROJECT_DIR
crontab /tmp/my-crontab
crontab -l
```

---

## 🚢 生产部署

### 部署前检查
```bash
pytest apps/**/test_e2e_*.py -v
python manage.py check --deploy
python manage.py collectstatic --noinput
./scripts/backup.sh production
```

### Docker部署
```bash
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml logs -f
```

---

## 📚 完整文档

详细文档请查看:
- **部署检查清单**: `DEPLOYMENT_CHECKLIST.md`
- **上线准备报告**: `PRODUCTION_READINESS_REPORT.md`
- **E2E测试总结**: `E2E_TEST_SUMMARY_FINAL.md`

---

**最后更新**: 2026-02-08
