# Скрипт подготовки к деплою HR Assistant Bot (Windows PowerShell)

Write-Host "🚀 Подготовка HR Assistant Bot к деплою..." -ForegroundColor Green
Write-Host ""

# Проверка наличия Git
try {
    git --version | Out-Null
    Write-Host "✅ Git найден" -ForegroundColor Green
} catch {
    Write-Host "❌ Git не установлен. Установите Git и попробуйте снова." -ForegroundColor Red
    Write-Host "   Скачайте: https://git-scm.com/download/win"
    exit 1
}

# Проверка наличия .env
if (-not (Test-Path .env)) {
    Write-Host "⚠️  Файл .env не найден!" -ForegroundColor Yellow
    Write-Host "Создайте .env файл с вашими ключами:"
    Write-Host "  TELEGRAM_BOT_TOKEN=your_token"
    Write-Host "  ANTHROPIC_API_KEY=your_key"
    Write-Host ""
    $continue = Read-Host "Продолжить без .env? (y/n)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        exit 1
    }
}

# Проверка .gitignore
if (-not (Test-Path .gitignore)) {
    Write-Host "⚠️  .gitignore не найден. Создаю..." -ForegroundColor Yellow
    @"
.env
.env.local
__pycache__/
*.pyc
venv/
"@ | Out-File -FilePath .gitignore -Encoding UTF8
    Write-Host "✅ .gitignore создан" -ForegroundColor Green
}

# Проверка, что .env в .gitignore
$gitignoreContent = Get-Content .gitignore
if ($gitignoreContent -notcontains ".env") {
    Write-Host "⚠️  Добавляю .env в .gitignore..." -ForegroundColor Yellow
    Add-Content -Path .gitignore -Value ".env"
    Write-Host "✅ .env добавлен в .gitignore" -ForegroundColor Green
}

Write-Host ""
Write-Host "📋 Проверка критичных файлов..." -ForegroundColor Cyan

# Список необходимых файлов
$files = @("hr_assistant_bot.py", "requirements.txt", "render.yaml", "Procfile")
$missing = $false

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file - НЕ НАЙДЕН!" -ForegroundColor Red
        $missing = $true
    }
}

if ($missing) {
    Write-Host ""
    Write-Host "❌ Некоторые файлы отсутствуют. Скопируйте все файлы из архива." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🔍 Проверка Git репозитория..." -ForegroundColor Cyan

# Инициализация Git если нужно
if (-not (Test-Path .git)) {
    Write-Host "Инициализирую Git репозиторий..."
    git init
    git branch -M main
    Write-Host "✅ Git репозиторий инициализирован" -ForegroundColor Green
} else {
    Write-Host "✅ Git репозиторий уже существует" -ForegroundColor Green
}

# Добавление файлов
Write-Host ""
Write-Host "📦 Добавление файлов в Git..." -ForegroundColor Cyan
git add .

# Проверка, что .env не добавлен
$envInGit = git ls-files .env 2>$null
if ($envInGit) {
    Write-Host "⚠️  ВНИМАНИЕ: .env файл в Git! Удаляю..." -ForegroundColor Yellow
    git rm --cached .env
    Write-Host "✅ .env удален из Git" -ForegroundColor Green
}

# Коммит
Write-Host ""
$commitMsg = Read-Host "Описание коммита (или Enter для 'Initial commit')"
if ([string]::IsNullOrWhiteSpace($commitMsg)) {
    $commitMsg = "Initial commit"
}

$status = git status --porcelain
if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Host "ℹ️  Нет изменений для коммита" -ForegroundColor Cyan
} else {
    git commit -m $commitMsg
    Write-Host "✅ Коммит создан: $commitMsg" -ForegroundColor Green
}

Write-Host ""
Write-Host "📋 Следующие шаги:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Создайте репозиторий на GitHub:"
Write-Host "   https://github.com/new"
Write-Host ""
Write-Host "2. Привяжите удаленный репозиторий:"
Write-Host "   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git"
Write-Host ""
Write-Host "3. Загрузите код:"
Write-Host "   git push -u origin main"
Write-Host ""
Write-Host "4. Разверните на Render.com:"
Write-Host "   - Зарегистрируйтесь: https://render.com"
Write-Host "   - New + → Web Service"
Write-Host "   - Подключите ваш GitHub репозиторий"
Write-Host "   - Добавьте переменные окружения:"
Write-Host "     * TELEGRAM_BOT_TOKEN"
Write-Host "     * ANTHROPIC_API_KEY"
Write-Host ""
Write-Host "✅ Подготовка завершена!" -ForegroundColor Green
Write-Host ""
Write-Host "💡 Подробные инструкции: DEPLOYMENT.md"
