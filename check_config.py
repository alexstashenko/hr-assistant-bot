#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для проверки конфигурации и работоспособности HR Assistant Bot
"""

import os
import sys
from dotenv import load_dotenv

def check_environment():
    """Проверка переменных окружения"""
    print("🔍 Проверка переменных окружения...\n")
    
    # Загружаем .env
    load_dotenv()
    
    errors = []
    warnings = []
    
    # Проверка Telegram токена
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not telegram_token:
        errors.append("❌ TELEGRAM_BOT_TOKEN не установлен")
    elif not telegram_token.strip():
        errors.append("❌ TELEGRAM_BOT_TOKEN пустой")
    elif len(telegram_token.split(':')) != 2:
        warnings.append("⚠️  TELEGRAM_BOT_TOKEN имеет неправильный формат (должен содержать ':')")
    else:
        print("✅ TELEGRAM_BOT_TOKEN: Установлен")
        print(f"   Формат: {telegram_token[:10]}...{telegram_token[-10:]}")
    
    # Проверка Anthropic API ключа
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        errors.append("❌ ANTHROPIC_API_KEY не установлен")
    elif not anthropic_key.strip():
        errors.append("❌ ANTHROPIC_API_KEY пустой")
    elif not anthropic_key.startswith("sk-ant-"):
        warnings.append("⚠️  ANTHROPIC_API_KEY не начинается с 'sk-ant-' (возможно неправильный формат)")
    else:
        print("✅ ANTHROPIC_API_KEY: Установлен")
        print(f"   Формат: {anthropic_key[:15]}...{anthropic_key[-10:]}")
    
    print()
    return errors, warnings

def check_dependencies():
    """Проверка установленных зависимостей"""
    print("📦 Проверка зависимостей...\n")
    
    dependencies = {
        'telegram': 'python-telegram-bot',
        'anthropic': 'anthropic',
        'dotenv': 'python-dotenv'
    }
    
    errors = []
    
    for module, package in dependencies.items():
        try:
            __import__(module)
            print(f"✅ {package}: Установлен")
        except ImportError:
            errors.append(f"❌ {package}: НЕ установлен")
            print(f"❌ {package}: НЕ установлен")
    
    print()
    return errors

def check_files():
    """Проверка наличия необходимых файлов"""
    print("📄 Проверка файлов...\n")
    
    required_files = [
        ('hr_assistant_bot.py', 'Основной файл бота'),
        ('requirements.txt', 'Файл зависимостей'),
    ]
    
    optional_files = [
        ('.env', 'Файл с переменными окружения'),
        ('README.md', 'Документация'),
        ('QUICKSTART.md', 'Быстрый старт'),
    ]
    
    errors = []
    warnings = []
    
    for filename, description in required_files:
        if os.path.exists(filename):
            print(f"✅ {filename}: Найден")
        else:
            errors.append(f"❌ {filename}: НЕ найден ({description})")
            print(f"❌ {filename}: НЕ найден")
    
    for filename, description in optional_files:
        if os.path.exists(filename):
            print(f"✅ {filename}: Найден")
        else:
            warnings.append(f"⚠️  {filename}: Не найден ({description})")
            print(f"⚠️  {filename}: Не найден")
    
    print()
    return errors, warnings

def check_telegram_connection():
    """Проверка подключения к Telegram"""
    print("🔗 Проверка подключения к Telegram...\n")
    
    try:
        from telegram import Bot
        load_dotenv()
        
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            print("❌ Токен не найден, пропускаем проверку подключения")
            return ["Токен не найден"]
        
        bot = Bot(token=token)
        bot_info = bot.get_me()
        
        print(f"✅ Подключение успешно!")
        print(f"   Имя бота: @{bot_info.username}")
        print(f"   ID: {bot_info.id}")
        print(f"   Полное имя: {bot_info.first_name}")
        
        print()
        return []
        
    except Exception as e:
        error = f"❌ Ошибка подключения: {str(e)}"
        print(error)
        print()
        return [error]

def check_anthropic_connection():
    """Проверка подключения к Anthropic API"""
    print("🤖 Проверка подключения к Anthropic API...\n")
    
    try:
        import anthropic
        load_dotenv()
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("❌ API ключ не найден, пропускаем проверку подключения")
            return ["API ключ не найден"]
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # Делаем минимальный тестовый запрос
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )
        
        print(f"✅ Подключение успешно!")
        print(f"   Модель: claude-sonnet-4-20250514")
        print(f"   Статус: Работает")
        
        print()
        return []
        
    except Exception as e:
        error = f"❌ Ошибка подключения: {str(e)}"
        print(error)
        print()
        return [error]

def main():
    """Главная функция проверки"""
    print("=" * 60)
    print("HR ASSISTANT BOT - Проверка конфигурации".center(60))
    print("=" * 60)
    print()
    
    all_errors = []
    all_warnings = []
    
    # Проверка файлов
    file_errors, file_warnings = check_files()
    all_errors.extend(file_errors)
    all_warnings.extend(file_warnings)
    
    # Проверка переменных окружения
    env_errors, env_warnings = check_environment()
    all_errors.extend(env_errors)
    all_warnings.extend(env_warnings)
    
    # Проверка зависимостей
    dep_errors = check_dependencies()
    all_errors.extend(dep_errors)
    
    # Если есть критические ошибки, останавливаемся
    if all_errors:
        print("=" * 60)
        print("❌ КРИТИЧЕСКИЕ ОШИБКИ:")
        for error in all_errors:
            print(f"   {error}")
        print()
        print("Исправьте ошибки перед запуском бота!")
        print("=" * 60)
        return False
    
    # Проверка подключений (только если нет критических ошибок)
    telegram_errors = check_telegram_connection()
    all_errors.extend(telegram_errors)
    
    anthropic_errors = check_anthropic_connection()
    all_errors.extend(anthropic_errors)
    
    # Итоговый отчет
    print("=" * 60)
    if all_errors:
        print("❌ ОБНАРУЖЕНЫ ОШИБКИ:")
        for error in all_errors:
            print(f"   {error}")
        print()
    
    if all_warnings:
        print("⚠️  ПРЕДУПРЕЖДЕНИЯ:")
        for warning in all_warnings:
            print(f"   {warning}")
        print()
    
    if not all_errors and not all_warnings:
        print("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ УСПЕШНО!".center(60))
        print()
        print("Бот готов к запуску!".center(60))
        print("Запустите: python hr_assistant_bot.py".center(60))
    elif not all_errors:
        print("✅ КРИТИЧЕСКИХ ОШИБОК НЕТ".center(60))
        print()
        print("Бот может работать, но есть предупреждения.".center(60))
        print("Запустите: python hr_assistant_bot.py".center(60))
    
    print("=" * 60)
    
    return not all_errors

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
