#!/bin/bash

# Скрипт подготовки к деплою HR Assistant Bot

set -e

echo "🚀 Подготовка HR Assistant Bot к деплою..."
echo ""

# Проверка наличия Git
if ! command -v git &> /dev/null; then
    echo "❌ Git не установлен. Установите Git и попробуйте снова."
    exit 1
fi

echo "✅ Git найден"

# Проверка наличия .env
if [ ! -f .env ]; then
    echo "⚠️  Файл .env не найден!"
    echo "Создайте .env файл с вашими ключами:"
    echo "  TELEGRAM_BOT_TOKEN=your_token"
    echo "  ANTHROPIC_API_KEY=your_key"
    echo ""
    read -p "Продолжить без .env? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Проверка .gitignore
if [ ! -f .gitignore ]; then
    echo "⚠️  .gitignore не найден. Создаю..."
    cat > .gitignore << 'EOF'
.env
.env.local
__pycache__/
*.pyc
venv/
EOF
    echo "✅ .gitignore создан"
fi

# Проверка, что .env в .gitignore
if ! grep -q "^\.env$" .gitignore; then
    echo "⚠️  Добавляю .env в .gitignore..."
    echo ".env" >> .gitignore
    echo "✅ .env добавлен в .gitignore"
fi

echo ""
echo "📋 Проверка критичных файлов..."

# Список необходимых файлов
files=("hr_assistant_bot.py" "requirements.txt" "render.yaml" "Procfile")
missing=0

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file - НЕ НАЙДЕН!"
        missing=1
    fi
done

if [ $missing -eq 1 ]; then
    echo ""
    echo "❌ Некоторые файлы отсутствуют. Скопируйте все файлы из архива."
    exit 1
fi

echo ""
echo "🔍 Проверка Git репозитория..."

# Инициализация Git если нужно
if [ ! -d .git ]; then
    echo "Инициализирую Git репозиторий..."
    git init
    git branch -M main
    echo "✅ Git репозиторий инициализирован"
else
    echo "✅ Git репозиторий уже существует"
fi

# Добавление файлов
echo ""
echo "📦 Добавление файлов в Git..."
git add .

# Проверка, что .env не добавлен
if git ls-files --error-unmatch .env 2>/dev/null; then
    echo "⚠️  ВНИМАНИЕ: .env файл в Git! Удаляю..."
    git rm --cached .env
    echo "✅ .env удален из Git"
fi

# Коммит
echo ""
read -p "Описание коммита (или Enter для 'Initial commit'): " commit_msg
commit_msg=${commit_msg:-"Initial commit"}

if git diff-index --quiet HEAD -- 2>/dev/null; then
    echo "ℹ️  Нет изменений для коммита"
else
    git commit -m "$commit_msg"
    echo "✅ Коммит создан: $commit_msg"
fi

echo ""
echo "📋 Следующие шаги:"
echo ""
echo "1. Создайте репозиторий на GitHub:"
echo "   https://github.com/new"
echo ""
echo "2. Привяжите удаленный репозиторий:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git"
echo ""
echo "3. Загрузите код:"
echo "   git push -u origin main"
echo ""
echo "4. Разверните на Render.com:"
echo "   - Зарегистрируйтесь: https://render.com"
echo "   - New + → Web Service"
echo "   - Подключите ваш GitHub репозиторий"
echo "   - Добавьте переменные окружения:"
echo "     * TELEGRAM_BOT_TOKEN"
echo "     * ANTHROPIC_API_KEY"
echo ""
echo "✅ Подготовка завершена!"
echo ""
echo "💡 Подробные инструкции: DEPLOYMENT.md"
