#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HR Assistant Telegram Bot
Сократис на базе Claude AI
"""

import os
import logging
import re
import json
from typing import Dict, List
from datetime import datetime
from pathlib import Path

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
import io

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Файлы для хранения данных
USER_DATA_FILE = "user_data.json"
CONVERSATIONS_DIR = "conversations"

# Системный промпт для Claude
SYSTEM_PROMPT = """## ИДЕНТИЧНОСТЬ

Ты — Сократис, навигатор смыслов, проводник через кризис среднего возраста для людей 45-60+. Помогаешь находить личные ответы через сократический диалог, не даёшь готовые решения.

**Ты НЕ:** психотерапевт, мотиватор с советами, робот с формальными ответами
**Ты ЕСТЬ:** мудрый собеседник, зеркало чувств, безопасное пространство для честного разговора

## ЦЕЛЕВАЯ АУДИТОРИЯ

Люди, переживающие экзистенциальный кризис: "половина жизни прошла впустую", ощущение бессмысленности, потерянности. Выросли в СССР/90-е, ценят честность, недоверчивы к коучам.

## МЕТОДОЛОГИЯ

### Основной подход: Сократический диалог
Не даёшь советы, задаёшь вопросы, ведущие к инсайтам:
- "Были ли моменты недавно, когда чувствовали себя живым?"
- "Что из текущего приносит ощущение 'это важно'?"
- "Если бы осталось 10 лет — что было бы обязательно?"

### Ключевые техники
**Анализ пути:** моменты радости → паттерны → "неудачи" как опыт
**Ценности:** что действительно важно, чьи ценности вы живёте?
**Наследие:** "Чему учить поколения? Какой след оставляю?"
**Смертность:** страх смерти → ограниченность времени как источник смысла
**Вторая половина:** "Какие возможности открываются сейчас?"

## ТОН И СТИЛЬ

**Говори на равных** — без менторства, признавай мудрость собеседника
**Будь человечным** — простые слова, разделяй эмоции, уместный юмор
**Держи пространство** — не торопи, комфортен с молчанием, не заполняй паузы советами
**Признавай сложность** — избегай упрощений типа "просто полюбите себя"

**Используй:** "Что вы чувствуете, когда...", "Расскажите подробнее", "Как бы вы сами ответили?"
**Избегай:** директив "вам нужно", обобщений, "я понимаю", жаргона, токсичного позитива

## ПРАКТИЧЕСКИЕ ВОПРОСЫ

- "Что вы делаете, забывая о времени?"
- "Если б деньги и мнение других не имели значения — чем бы занимались?"
- "Когда последний раз делали что-то впервые?"
- "Что научили вас ваши 'неудачи'?"
- "Кем вы были до того, как мир сказал вам, кем быть?"

## УПРАЖНЕНИЯ

**Дневник живости:** ежедневно записывать 1 момент подлинной живости
**Письмо в прошлое:** письмо себе в 30 лет — совет, предупреждение, благодарность
**Эксперимент с 5 годами:** что ОБЯЗАТЕЛЬНО сделать, если осталось ровно 5 лет?
**Инвентаризация ценностей:** 10 важных вещей + сколько времени на каждое → выявить несоответствие
**Третье лицо:** описать свою жизнь как о другом человеке — что посоветуешь ему?

## ГРАНИЦЫ И КРИТИЧЕСКИЕ СИТУАЦИИ

### МОЖЕШЬ:
Задавать вопросы, быть свидетелем, предлагать перспективы, делиться упражнениями

### НЕ МОЖЕШЬ:
Ставить диагнозы, проводить психотерапию, давать медсоветы, решать вместо человека

### При суицидальных мыслях:
"Спасибо за доверие. Это серьёзно — пожалуйста, обратитесь к специалисту:
- Телефон доверия: 8-800-2000-122 (24/7, бесплатно)
- Психотерапевт/психиатр
- Критическое состояние — скорая: 112"

### При признаках клинической депрессии:
"Вам нужна профессиональная помощь. Я могу поддержать поиск смысла, но не заменю врача. Рекомендую психотерапевта или психиатра."

## СТРУКТУРА СЕССИИ

**Первая встреча:**
1. Создай безопасность
2. Выясни запрос
3. Признай боль
4. Дай надежду
5. Установи процесс: "Я не даю готовых ответов, помогу найти ваши"

**Последующие:**
1. Рефлексия: "Что изменилось?"
2. Углубление: одна тема глубоко
3. Практика: простое упражнение
4. Якорь: "Что откликнулось больше всего?"

## ЧЕКЛИСТ ДЛЯ КАЖДОГО ОТВЕТА

- [ ] Задал вопрос вместо совета?
- [ ] Признал эмоции?
- [ ] Избегаю жаргона и директив?
- [ ] Говорю на равных?
- [ ] Критический риск (суицид, депрессия)?

## АДАПТАЦИЯ К СОСТОЯНИЮ

- **Острая боль:** эмпатия > вопросы
- **Злость:** признай право на гнев
- **Апатия:** мягкие простые вопросы
- **Любопытство:** исследуй глубже

---

**Главное:** Ты компас, не карта. Указываешь направление, человек проходит путь сам.

Общайся кратко. Задавай вопросы по одному и дожидайся ответа пользователя."""


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


def clean_markdown(text: str) -> str:
    """Удаляет markdown форматирование из текста для чистого отображения в Telegram"""
    try:
        # Удаляем жирный текст (**text** или __text__)
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)
        
        # Удаляем курсив простым способом
        text = text.replace('*', '')
        text = text.replace('_', '')
        
        # Удаляем заголовки (# ## ### и т.д.)
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        
        # Удаляем блоки кода
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        
        # Удаляем инлайн код
        text = re.sub(r'`([^`]+)`', r'\1', text)
        
        # Удаляем тильды
        text = text.replace('~~', '')
        
        return text.strip()
    except Exception as e:
        # Если что-то пошло не так, вернем оригинальный текст
        logger.warning(f"Error in clean_markdown: {e}")
        return text


class HRAssistantBot:
    """Класс для управления HR-ассистентом ботом"""
    
    def __init__(self, telegram_token: str, anthropic_api_key: str, admin_telegram_id: int):
        """
        Инициализация бота
        
        Args:
            telegram_token: Токен Telegram бота
            anthropic_api_key: API ключ Anthropic
            admin_telegram_id: Telegram ID администратора
        """
        self.telegram_token = telegram_token
        self.anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
        self.admin_telegram_id = admin_telegram_id
        
        # Хранилище истории разговоров по пользователям (только для контекста)
        self.conversations: Dict[int, List[Dict]] = {}
        
        # Создаем директорию для хранения истории переписок
        Path(CONVERSATIONS_DIR).mkdir(exist_ok=True)
        
        # Загружаем данные о пользователях из файла
        self.user_data = self.load_user_data()
        
        # Telegram Application (будет установлен в run())
        self.application = None
        
    def load_user_data(self) -> Dict:
        """Загрузить данные о пользователях из файла"""
        if Path(USER_DATA_FILE).exists():
            try:
                with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Загружены данные о {len(data)} пользователях")
                    return data
            except Exception as e:
                logger.error(f"Ошибка при загрузке данных пользователей: {e}")
                return {}
        return {}
    
    def save_user_data(self):
        """Сохранить данные о пользователях в файл"""
        try:
            with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.user_data, f, ensure_ascii=False, indent=2)
            logger.info("Данные пользователей сохранены")
        except Exception as e:
            logger.error(f"Ошибка при сохранении данных пользователей: {e}")
    
    def save_conversation_to_file(self, user_id: int):
        """Сохранить историю переписки пользователя в файл"""
        try:
            conversation_file = Path(CONVERSATIONS_DIR) / f"user_{user_id}.json"
            with open(conversation_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversations.get(user_id, []), f, ensure_ascii=False, indent=2)
            logger.info(f"История переписки пользователя {user_id} сохранена")
        except Exception as e:
            logger.error(f"Ошибка при сохранении истории переписки: {e}")
    
    def load_conversation_from_file(self, user_id: int) -> List[Dict]:
        """Загрузить историю переписки пользователя из файла"""
        conversation_file = Path(CONVERSATIONS_DIR) / f"user_{user_id}.json"
        if conversation_file.exists():
            try:
                with open(conversation_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Ошибка при загрузке истории переписки: {e}")
                return []
        return []
    
    def get_user_info(self, user_id: int) -> Dict:
        """Получить информацию о пользователе"""
        user_id_str = str(user_id)
        if user_id_str not in self.user_data:
            self.user_data[user_id_str] = {
                "message_count": 0,
                "demo_completed_notified": False,
                "first_seen": datetime.now().isoformat(),
                "username": None,
                "first_name": None
            }
            self.save_user_data()
        return self.user_data[user_id_str]
    
    def update_user_info(self, user_id: int, username: str = None, first_name: str = None):
        """Обновить информацию о пользователе"""
        user_info = self.get_user_info(user_id)
        if username:
            user_info["username"] = username
        if first_name:
            user_info["first_name"] = first_name
        self.save_user_data()
    
    def get_message_limit(self, user_id: int) -> int:
        """Получить лимит сообщений для пользователя"""
        if user_id == self.admin_telegram_id:
            return 1000
        return 10
    
    def get_remaining_messages(self, user_id: int) -> int:
        """Получить количество оставшихся сообщений"""
        limit = self.get_message_limit(user_id)
        user_info = self.get_user_info(user_id)
        used = user_info.get("message_count", 0)
        return max(0, limit - used)
    
    def increment_message_count(self, user_id: int):
        """Увеличить счетчик сообщений"""
        user_info = self.get_user_info(user_id)
        user_info["message_count"] = user_info.get("message_count", 0) + 1
        self.save_user_data()
        
        logger.info(
            f"User {user_id}: сообщение {user_info['message_count']}/{self.get_message_limit(user_id)}"
        )
    
    def has_messages_left(self, user_id: int) -> bool:
        """Проверить, есть ли у пользователя оставшиеся сообщения"""
        return self.get_remaining_messages(user_id) > 0
    
    def reset_user_limit(self, user_id: int):
        """Сбросить лимит пользователя (только для админа)"""
        user_info = self.get_user_info(user_id)
        user_info["message_count"] = 0
        user_info["demo_completed_notified"] = False
        self.save_user_data()
        logger.info(f"Админ сбросил лимит для пользователя {user_id}")
    
    def format_conversation_as_text(self, user_id: int) -> str:
        """Форматировать историю переписки в текстовый формат"""
        conversation = self.conversations.get(user_id, [])
        user_info = self.get_user_info(user_id)

        # Инициализируем переменную text
        text = ""
        
        # Заголовок
        text += f"ИСТОРИЯ ПЕРЕПИСКИ\n"
        text += f"Пользователь: {user_info.get('first_name', 'Не указано')}\n"
        text += f"Username: @{user_info.get('username', 'не указан')}\n"
        text += f"Telegram ID: {user_id}\n"
        text += f"Дата первого сообщения: {user_info.get('first_seen', 'Не указана')}\n"
        text += f"Всего сообщений: {len(conversation)}\n"
        text += f"Дата завершения демо: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
        text += f"\n" + "=" * 80 + "\n\n"
        
        # Переписка
        for i, msg in enumerate(conversation, 1):
            role = "ПОЛЬЗОВАТЕЛЬ" if msg["role"] == "user" else "АССИСТЕНТ"
            text += f"[{i}] {role}:\n"
            text += f"{msg['content']}\n\n"
        
        text += "КОНЕЦ ИСТОРИИ ПЕРЕПИСКИ\n"
        
        return text
    
    async def send_conversation_history(self, user_id: int):
        """Отправить историю переписки администратору"""
        try:
            # Форматируем историю в текст
            conversation_text = self.format_conversation_as_text(user_id)
            
            # Создаем файл в памяти
            text_file = io.BytesIO(conversation_text.encode('utf-8'))
            text_file.name = f"conversation_user_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            user_info = self.get_user_info(user_id)
            caption = (
                f"История переписки пользователя:\n\n"
                f"{user_info.get('first_name', 'Не указано')}\n"
                f"@{user_info.get('username', 'не указан')}\n"
                f"{user_id}\n"
                f"Сообщений: {len(self.conversations.get(user_id, []))}"
            )
            
            # Отправляем файл админу
            await self.application.bot.send_document(
                chat_id=self.admin_telegram_id,
                document=text_file,
                caption=caption,
                filename=text_file.name
            )
            
            logger.info(f"История переписки пользователя {user_id} отправлена админу")
            
        except Exception as e:
            logger.error(f"Ошибка при отправке истории переписки админу: {e}")
    
    async def notify_admin_demo_complete(self, user_id: int, username: str, first_name: str):
        """Отправить уведомление администратору о завершении демо с историей переписки"""
        try:
            # Сначала отправляем короткое уведомление
            message = (
                f"УВЕДОМЛЕНИЕ: Пользователь завершил ДЕМО\n\n"
                f"Имя: {first_name or 'Не указано'}\n"
                f"Username: @{username or 'не указан'}\n"
                f"Telegram ID: {user_id}\n"
                f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n"
                f"Пользователь исчерпал 10 бесплатных сообщений.\n\n"
                f"📎 История переписки прикреплена ниже."
            )
            
            await self.application.bot.send_message(
                chat_id=self.admin_telegram_id,
                text=message
            )
            
            # Затем отправляем файл с историей переписки
            await self.send_conversation_history(user_id)
            
            # Сохраняем историю в файл для архива
            self.save_conversation_to_file(user_id)
            
            # Помечаем, что уведомление отправлено
            user_info = self.get_user_info(user_id)
            user_info["demo_completed_notified"] = True
            self.save_user_data()
            
            logger.info(f"Отправлено уведомление админу о завершении демо пользователем {user_id}")
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления админу: {e}")
    
    def get_conversation_history(self, user_id: int) -> List[Dict]:
        """Получить историю разговора пользователя"""
        if user_id not in self.conversations:
            # Пробуем загрузить из файла
            self.conversations[user_id] = self.load_conversation_from_file(user_id)
        return self.conversations[user_id]
    
    def add_message_to_history(self, user_id: int, role: str, content: str):
        """Добавить сообщение в историю"""
        if user_id not in self.conversations:
            self.conversations[user_id] = self.load_conversation_from_file(user_id)
        
        self.conversations[user_id].append({
            "role": role,
            "content": content
        })
        
        # Сохраняем в файл после каждого сообщения
        self.save_conversation_to_file(user_id)
        
        # Ограничиваем историю последними 20 сообщениями (10 пар) для контекста Claude
        # Но полная история сохраняется в файл
        if len(self.conversations[user_id]) > 20:
            # Оставляем только последние 20 для контекста
            context_history = self.conversations[user_id][-20:]
            self.conversations[user_id] = context_history
    
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
            
            # Получаем историю разговора (последние 20 сообщений для контекста)
            conversation_history = self.get_conversation_history(user_id)
            
            # Логируем количество сообщений для мониторинга
            logger.info(f"User {user_id}: отправляем {len(conversation_history)} сообщений в историю")
            
            # Отправляем запрос к Claude
            response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=conversation_history
            )
            
            # Логируем использование токенов
            logger.info(
                f"User {user_id}: input_tokens={response.usage.input_tokens}, "
                f"output_tokens={response.usage.output_tokens}"
            )
            
            # Извлекаем ответ
            assistant_message = response.content[0].text
            
            # Очищаем от markdown форматирования для чистого текста в Telegram
            assistant_message = clean_markdown(assistant_message)
            
            # Добавляем ответ ассистента в историю
            self.add_message_to_history(user_id, "assistant", assistant_message)
            
            return assistant_message
            
        except Exception as e:
            logger.error(f"Ошибка при получении ответа от Claude: {e}")
            logger.error(f"Тип ошибки: {type(e).__name__}")
            logger.error(f"Детали: {str(e)}")
            return "Извините, произошла ошибка при обработке вашего запроса. Попробуйте еще раз."
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        user_id = user.id
        
        # Обновляем информацию о пользователе
        self.update_user_info(user_id, user.username, user.first_name)
        
        # Проверяем, есть ли доступ
        if not self.has_messages_left(user_id):
            await update.message.reply_text(
                "ДЕМО-РЕЖИМ ЗАВЕРШЕН\n\n"
                "Вы исчерпали 10 бесплатных сообщений.\n\n"
                "Надеемся, что этот разговор был полезным!\n\n"
                "Если вы хотите продолжить общение с ИИ-ассистентом, "
                "обратитесь к @alexander_stashenko\n\n"
                "Спасибо! 🙏"
            )
            return
        
        # Получаем лимит сообщений
        remaining = self.get_remaining_messages(user_id)
        limit = self.get_message_limit(user_id)
        
        demo_info = ""
        if limit == 10:
            demo_info = f"\n\nДЕМО-РЕЖИМ: У вас {remaining} сообщений"
        
        welcome_message = (
            f"Здравствуйте! Со мной можно поговорить о жизни и ее смыслах.\n\n"
            "Расскажите - что вас беспокоит, о чем думаете?"
            
            f"{demo_info}\n\n"
        )
        
        await update.message.reply_text(welcome_message)
        logger.info(f"Пользователь {user_id} ({user.username}) начал работу с ботом")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        user_id = update.effective_user.id
        remaining = self.get_remaining_messages(user_id)
        limit = self.get_message_limit(user_id)
        
        demo_info = ""
        if limit == 10:
            demo_info = f"\n\nДЕМО-РЕЖИМ: Осталось {remaining} из {limit} сообщений"
        
        help_message = (
            "Как работать с ботом:\n\n"
            f"{demo_info}"
        )
        
        await update.message.reply_text(help_message)
    
    async def grant_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /grant для сброса лимита (только для админа)"""
        user_id = update.effective_user.id
        
        # Проверяем, что команду вызвал админ
        if user_id != self.admin_telegram_id:
            await update.message.reply_text("У вас нет прав для выполнения этой команды.")
            return
        
        # Проверяем формат команды
        if not context.args or len(context.args) != 1:
            await update.message.reply_text(
                "Использование: /grant <user_id>\n\n"
                "Пример: /grant 123456789\n\n"
                "Эта команда сбрасывает счетчик сообщений пользователя до 10."
            )
            return
        
        try:
            target_user_id = int(context.args[0])
            
            # Сбрасываем лимит пользователя
            self.reset_user_limit(target_user_id)
            
            user_info = self.get_user_info(target_user_id)
            username = user_info.get("username", "неизвестен")
            first_name = user_info.get("first_name", "Неизвестно")
            
            await update.message.reply_text(
                f"✅ Лимит сброшен!\n\n"
                f"Пользователь: {first_name}\n"
                f"Username: @{username}\n"
                f"ID: {target_user_id}\n\n"
                f"Пользователь получил новые 10 сообщений."
            )
            
            logger.info(f"Админ {user_id} сбросил лимит пользователю {target_user_id}")
            
        except ValueError:
            await update.message.reply_text("❌ Ошибка: ID пользователя должен быть числом.")
        except Exception as e:
            await update.message.reply_text(f"❌ Произошла ошибка: {str(e)}")
            logger.error(f"Ошибка при сбросе лимита: {e}")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user = update.effective_user
        user_id = user.id
        user_message = update.message.text
        
        # Обновляем информацию о пользователе
        self.update_user_info(user_id, user.username, user.first_name)
        
        logger.info(f"Сообщение от {user_id} ({user.username}): {user_message[:50]}...")
        
        # Проверяем, есть ли у пользователя оставшиеся сообщения
        if not self.has_messages_left(user_id):
            # Отправляем уведомление админу, если еще не отправляли
            user_info = self.get_user_info(user_id)
            if not user_info.get("demo_completed_notified", False):
                await self.notify_admin_demo_complete(
                    user_id,
                    user.username or "не указан",
                    user.first_name or "Не указано"
                )
            
            await update.message.reply_text(
                "ДЕМО-РЕЖИМ ЗАВЕРШЕН\n\n"
                "Вы исчерпали 10 бесплатных сообщений.\n\n"
                "Надеемся, что этот разговор был полезным!\n\n"
                "Если вы хотите продолжить общение с ИИ-ассистентом, "
                "обратитесь к @alexander_stashenko\n\n"
                "Спасибо! 🙏"
            )
            return
        
        # Увеличиваем счетчик сообщений
        self.increment_message_count(user_id)
        
        # Получаем количество оставшихся сообщений
        remaining = self.get_remaining_messages(user_id)
        
        # Показываем индикатор печати
        await update.message.chat.send_action("typing")
        
        # Получаем ответ от Claude
        response = await self.get_claude_response(user_id, user_message)
        
        # Добавляем информацию об оставшихся сообщениях для демо-пользователей
        if self.get_message_limit(user_id) == 10:
            if remaining <= 3:  # Предупреждаем, когда остается мало
                response += f"\n\n⚠️ Осталось сообщений: {remaining}"
            elif remaining == 5:  # Предупреждение на половине
                response += f"\n\n📊 Осталось сообщений: {remaining}"
        
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
        
        # Если у пользователя закончились сообщения после этого ответа
        if remaining == 0:
            await self.notify_admin_demo_complete(
                user_id,
                user.username or "не указан",
                user.first_name or "Не указано"
            )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        logger.error(f"Произошла ошибка: {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "Извините, произошла ошибка. Попробуйте еще раз."
            )
    
    def run(self):
        """Запустить бота"""
        # Запускаем health check сервер для облачных платформ (Render, Railway, etc.)
        start_health_server()
        
        # Создаем приложение
        self.application = Application.builder().token(self.telegram_token).build()
        
        # Регистрируем обработчики команд
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("grant", self.grant_command))
        
        # Регистрируем обработчик текстовых сообщений
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Регистрируем обработчик ошибок
        self.application.add_error_handler(self.error_handler)
        
        # Запускаем бота
        logger.info("Бот запущен и готов к работе!")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Главная функция"""
    # Получаем токены из переменных окружения
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    admin_telegram_id = os.getenv("ADMIN_TELEGRAM_ID")
    
    if not telegram_token:
        raise ValueError("Не установлена переменная окружения TELEGRAM_BOT_TOKEN")
    
    if not anthropic_api_key:
        raise ValueError("Не установлена переменная окружения ANTHROPIC_API_KEY")
    
    if not admin_telegram_id:
        raise ValueError("Не установлена переменная окружения ADMIN_TELEGRAM_ID")
    
    try:
        admin_telegram_id = int(admin_telegram_id)
    except ValueError:
        raise ValueError("ADMIN_TELEGRAM_ID должен быть числом")
    
    # Создаем и запускаем бота
    bot = HRAssistantBot(telegram_token, anthropic_api_key, admin_telegram_id)
    bot.run()


if __name__ == "__main__":
    main()
