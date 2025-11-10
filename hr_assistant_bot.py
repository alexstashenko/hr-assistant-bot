#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HR Assistant Telegram Bot
Консультант по управлению персоналом на базе Claude AI
"""

import os
import logging
from typing import Dict, List
from datetime import datetime
import anthropic
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import re

# Отключаем телеметрию Anthropic
os.environ['ANTHROPIC_DISABLE_TELEMETRY'] = 'true'

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()

# Системный промпт для Claude
SYSTEM_PROMPT = """# **РОЛЬ: Ассистент по управлению персоналом**

Вы — опытный консультант по управлению людьми, который помогает руководителям эффективно работать со своими подчиненными. Ваша задача — давать краткие, практичные, применимые на практике рекомендации.

---

## **ОБЛАСТИ ЭКСПЕРТИЗЫ:**

- Мотивация сотрудников
- Постановка задач и целей
- Делегирование полномочий
- Обратная связь (позитивная и конструктивная)
- Развитие и рост сотрудников
- Разрешение конфликтов
- Управление производительностью
- Адаптация новых сотрудников (onboarding)
- Управление выгоранием и перегрузкой
- Сложные разговоры (увольнения, понижения, отказы)
- Работа с underperformance
- Удержание ключевых сотрудников

---

## **БАЗОВЫЕ МОДЕЛИ И ФРЕЙМВОРКИ:**

### **Модель PAEI Адизеса**
Используйте для диагностики типа сотрудника и подбора подхода:
- **P (Producer)** — Производитель: делает, достигает результатов, фокус на "что"
- **A (Administrator)** — Администратор: систематизирует, организует, фокус на "как"
- **E (Entrepreneur)** — Предприниматель: генерирует идеи, меняет, фокус на "зачем/что если"
- **I (Integrator)** — Интегратор: объединяет команду, создает атмосферу, фокус на "кто"

**Применение:** Определите доминирующий стиль сотрудника, чтобы правильно мотивировать, делегировать и давать обратную связь.

### **Ситуационное лидерство Херси-Бланшара**
Выбирайте стиль управления в зависимости от уровня зрелости сотрудника:

**Уровень зрелости = Компетентность × Мотивация**

- **S1 — Директивный** (Низкая компетентность + Низкая мотивация): Четкие инструкции, контроль, структура
- **S2 — Наставнический** (Низкая компетентность + Высокая мотивация): Объяснения, обучение, поддержка
- **S3 — Поддерживающий** (Высокая компетентность + Низкая мотивация): Вовлечение, обсуждение, вдохновение
- **S4 — Делегирующий** (Высокая компетентность + Высокая мотивация): Автономия, доверие, минимальный контроль

**Применение:** Перед рекомендациями оцените, на каком уровне находится сотрудник, и предложите соответствующий стиль.

---

## **АЛГОРИТМ РАБОТЫ:**

### **Шаг 0: Быстрая диагностика**
Перед вопросами мысленно определите тип ситуации:
- Проблема производительности vs. поведенческая проблема
- Новый сотрудник vs. опытный
- Острая ситуация vs. хроническая
- Индивидуальная vs. командная проблема

### **Шаг 1: Уточнение ситуации**
Когда руководитель обращается с проблемой, задайте по одному вопросу за раз, дожидайтесь ответа:

**Базовые вопросы:**
1. Что уже было предпринято?
2. Как долго длится ситуация?
3. Какова специфика сотрудника (опыт, роль, особенности)?
4. Каков желаемый результат?

**Контекстные вопросы (при необходимости):**
- Размер вашей команды?
- Ваш опыт в роли руководителя (новый/опытный)?
- Есть ли ограничения (политика компании, сроки, бюджет)?
- Корпоративная культура (формальная/свободная, иерархичная/плоская)?

### **Шаг 2: Анализ и рекомендации**

После получения ответов предоставьте структурированный ответ:

**1. ДИАГНОСТИКА (2-3 предложения)**
- Корень проблемы
- Тип сотрудника по PAEI (если применимо)
- Уровень зрелости по Херси-Бланшару (S1/S2/S3/S4)

**2. ПЛАН ДЕЙСТВИЙ**

**Шаг 1: Первое действие (сегодня-завтра)**
- Что конкретно сделать
- Пример формулировки/скрипт разговора

**Шаг 2: Следующие шаги (на этой неделе)**
- Конкретные действия

**Шаг 3: Закрепление результата**
- Как поддержать изменения

**3. ЧТО СКАЗАТЬ**
Готовые формулировки или скрипты для разговора

**4. ЧЕГО ИЗБЕГАТЬ**
Топ-3 распространенные ошибки в данной ситуации

**5. ПРИЗНАКИ УСПЕХА**
Как понять, что подход работает (конкретные индикаторы)

**6. КРАСНЫЕ ФЛАГИ** (если применимо)
Признаки, требующие немедленного внимания HR/юриста:
- Угрозы, агрессия, конфликт интересов
- Дискриминация, харассмент
- Признаки выгорания или психологического кризиса
- Нарушения этики/комплаенса

---

## **БЫСТРЫЕ ШАБЛОНЫ**

Для типовых ситуаций давайте готовые мини-скрипты:

**Сложная обратная связь:**
"[Имя], я хочу обсудить [конкретная ситуация]. Я заметил [факт без оценки]. Это влияет на [последствия]. Давай вместе разберемся, что происходит?"

**Отказ в повышении/премии:**
"Ценю твой вклад в [конкретные достижения]. Сейчас решение по повышению — [причина]. Чтобы двигаться к этой цели, нужно [конкретные шаги]. Готов поддержать тебя в этом."

**Делегирование задачи:**
"У меня есть задача [название]. Результат должен быть [описание]. Ресурсы: [что доступно]. Срок: [когда]. Что тебе нужно от меня для успеха?"

**1-on-1 встреча:**
"Три вопроса: Как у тебя дела? Что тебе сейчас нужно от меня? Что я могу сделать лучше как руководитель?"

---

## **СТИЛЬ ОБЩЕНИЯ:**

- Общайтесь в пользователем на "вы"
- Пишите конкретно и по делу — никакой воды
- Давайте примеры фраз и действий, а не абстрактные советы
- Будьте эмпатичным к обеим сторонам (руководителю и сотруднику)
- Учитывайте реальность бизнеса (сроки, ресурсы, политику компании)
- Если ситуация требует вмешательства HR или юриста — скажите об этом прямо
- Фокус на быстрых точечных решениях

---

## **ВАЖНЫЕ ПРИНЦИПЫ:**

1. Каждый сотрудник уникален — нет универсальных решений
2. Сначала понять, потом действовать — диагностика важнее скорости
3. Фокус на поведении и результатах, а не на личности
4. Развитие важнее наказания — но есть ситуации, требующие жестких мер
5. Документирование важных разговоров — хорошая практика (особенно при проблемах)
6. Баланс между срочностью бизнеса и развитием людей — помогай руководителю найти эту грань
7. Адаптируйте стиль под ситуацию — используй модели PAEI и Херси-Бланшара

---

## **НАЧАЛО РАБОТЫ:**

Начинайте работу после того, как руководитель опишет свою ситуацию. 

Задавайте вопросы по одному за раз, дожидайся ответа, затем следующий вопрос."""


def escape_markdown_v2(text: str) -> str:
    """Экранирует спецсимволы для MarkdownV2"""
    # Спецсимволы, которые нужно экранировать в MarkdownV2
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text


class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP handler для health checks облачных платформ"""
    
    def do_GET(self):
        """Обработка GET запросов для проверки здоровья"""
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'HR Assistant Bot is running')
    
    def log_message(self, format, *args):
        """Отключаем логирование health check запросов"""
        pass


def start_health_server():
    """Запуск HTTP сервера для health checks"""
    port = int(os.getenv('PORT', 8080))
    try:
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        logger.info(f"Health check server started on port {port}")
    except Exception as e:
        logger.warning(f"Could not start health check server: {e}")


class HRAssistantBot:
    """Класс для управления HR-ассистентом ботом"""
    
    def __init__(self, telegram_token: str, anthropic_api_key: str):
        """
        Инициализация бота
        
        Args:
            telegram_token: Токен Telegram бота
            anthropic_api_key: API ключ Anthropic
        """
        self.telegram_token = telegram_token
        self.anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
        
        # Хранилище истории разговоров по пользователям
        self.conversations: Dict[int, List[Dict]] = {}
        
    def get_conversation_history(self, user_id: int) -> List[Dict]:
        """Получить историю разговора пользователя"""
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        return self.conversations[user_id]
    
    def add_message_to_history(self, user_id: int, role: str, content: str):
        """Добавить сообщение в историю"""
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        self.conversations[user_id].append({
            "role": role,
            "content": content
        })
        
        # Ограничиваем историю последними 20 сообщениями (10 пар)
        if len(self.conversations[user_id]) > 20:
            self.conversations[user_id] = self.conversations[user_id][-20:]
    
    def clear_conversation(self, user_id: int):
        """Очистить историю разговора"""
        self.conversations[user_id] = []
    
    async def get_claude_response(self, user_id: int, user_message: str) -> str:
        """
        Получить ответ от Claude
        
        Args:
            user_id: ID пользователя Telegram
            user_message: Сообщение пользователя
            
        Returns:
            Ответ Claude
        """
        try:
            # Добавляем сообщение пользователя в историю
            self.add_message_to_history(user_id, "user", user_message)
            
            # Получаем историю разговора
            conversation_history = self.get_conversation_history(user_id)
            
            # Отправляем запрос к Claude
            response = self.anthropic_client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=conversation_history
            )
            
            # Извлекаем ответ
            assistant_message = response.content[0].text
            
            # Добавляем ответ ассистента в историю
            self.add_message_to_history(user_id, "assistant", assistant_message)
            
            return assistant_message
            
        except Exception as e:
            logger.error(f"Ошибка при получении ответа от Claude: {e}")
            return "Извините, произошла ошибка при обработке вашего запроса. Попробуйте еще раз."
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        user_id = user.id
        
        # Очищаем историю при старте
        self.clear_conversation(user_id)
        
        welcome_message = (
            f"Здравствуйте, {user.first_name}!\n\n"
            "Я — ваш персональный консультант по управлению персоналом на базе Claude AI.\n\n"
            "Я помогу вам:\n"
            "• Мотивировать сотрудников\n"
            "• Давать эффективную обратную связь\n"
            "• Решать конфликты в команде\n"
            "• Управлять производительностью\n"
            "• Проводить сложные разговоры\n"
            "• И многое другое!\n\n"
            "Просто опишите вашу ситуацию, и я задам уточняющие вопросы, "
            "чтобы дать вам конкретные практичные рекомендации.\n\n"
            "Используйте команды:\n"
            "/start — начать работу с ботом\n"
            "/help — справка по использованию\n\n"
            "Давайте начнем! Какая ситуация вас беспокоит?"
        )
        
        await update.message.reply_text(welcome_message)
        logger.info(f"Пользователь {user_id} ({user.username}) начал работу с ботом")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_message = (
            "Как работать с ботом:\n\n"
            "1. Опишите вашу ситуацию или проблему с сотрудником/командой\n"
            "2. Я задам уточняющие вопросы (по одному)\n"
            "3. После уточнений вы получите:\n"
            "   • Диагностику ситуации\n"
            "   • Конкретный план действий\n"
            "   • Готовые скрипты разговоров\n"
            "   • Предупреждения о возможных ошибках\n\n"
            "Доступные команды:\n"
            "/start — начать работу с ботом\n"
            "/help — показать эту справку\n\n"
            "Примеры запросов:\n"
            "• Мой сотрудник перестал выполнять задачи в срок\n"
            "• Как дать обратную связь о плохой работе?\n"
            "• Два члена команды конфликтуют между собой\n"
            "• Нужно отказать в повышении\n\n"
            "Я использую проверенные модели управления (PAEI Адизеса, "
            "Ситуационное лидерство Херси-Бланшара) для диагностики и рекомендаций."
        )
        
        await update.message.reply_text(help_message)
    
    async def new_conversation_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /new для начала нового разговора"""
        user_id = update.effective_user.id
        self.clear_conversation(user_id)
        
        await update.message.reply_text(
            "История разговора очищена. Начнем с начала!\n\n"
            "Опишите новую ситуацию, с которой вам нужна помощь."
        )
        logger.info(f"Пользователь {user_id} начал новый разговор")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user = update.effective_user
        user_id = user.id
        user_message = update.message.text
        
        logger.info(f"Сообщение от {user_id} ({user.username}): {user_message[:50]}...")
        
        # Показываем индикатор печати
        await update.message.chat.send_action("typing")
        
        # Получаем ответ от Claude
        response = await self.get_claude_response(user_id, user_message)
        
        # Telegram имеет ограничение на длину сообщения (4096 символов)
        # Если ответ длиннее, разбиваем на части
        if len(response) <= 4096:
            await update.message.reply_text(response)
        else:
            # Разбиваем на части по 4000 символов
            parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for part in parts:
                await update.message.reply_text(part)
                await update.message.chat.send_action("typing")
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        logger.error(f"Произошла ошибка: {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "Извините, произошла ошибка. Попробуйте еще раз или используйте /new для начала нового разговора."
            )
    
    def run(self):
        """Запустить бота"""
        # Запускаем health check сервер для облачных платформ (Render, Railway, etc.)
        start_health_server()
        
        # Создаем приложение
        application = Application.builder().token(self.telegram_token).build()
        
        # Регистрируем обработчики команд
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("new", self.new_conversation_command))
        
        # Регистрируем обработчик текстовых сообщений
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Регистрируем обработчик ошибок
        application.add_error_handler(self.error_handler)
        
        # Запускаем бота
        logger.info("Бот запущен и готов к работе!")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Главная функция"""
    # Получаем токены из переменных окружения
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not telegram_token:
        raise ValueError("Не установлена переменная окружения TELEGRAM_BOT_TOKEN")
    
    if not anthropic_api_key:
        raise ValueError("Не установлена переменная окружения ANTHROPIC_API_KEY")
    
    # Создаем и запускаем бота
    bot = HRAssistantBot(telegram_token, anthropic_api_key)
    bot.run()


if __name__ == "__main__":
    main()
