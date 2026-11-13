import requests
import logging
import os 
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURACIÓN ---

# Ahora leemos las variables del entorno del servidor
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
DIFY_API_KEY = os.environ.get("DIFY_API_KEY")

# URL de la API de Dify (Cambia esto si usas una instancia self-hosted)
DIFY_API_URL = "https://api.dify.ai/v1/chat-messages" 
# Si usas Dify Cloud estándar, la URL suele ser: https://api.dify.ai/v1/chat-messages
# Si es self-hosted, será algo como: http://localhost:80/api/v1/chat-messages

# --- LÓGICA DEL BOT ---

# Diccionario para guardar los conversation_id de cada usuario
user_conversations = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Soy tu asistente conectado a Dify. Escribe algo para empezar.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_message = update.message.text
    
    # Obtener o crear conversation_id para mantener el contexto
    conversation_id = user_conversations.get(user_id, "")

    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "inputs": {},
        "query": user_message,
        "response_mode": "blocking", # Espera a tener la respuesta completa
        "conversation_id": conversation_id,
        "user": user_id
    }

    try:
        # Enviar mensaje a Dify
        response = requests.post(DIFY_API_URL, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()

        # Guardar el nuevo conversation_id para la próxima vez
        user_conversations[user_id] = result.get("conversation_id", "")
        
        # Enviar respuesta de vuelta a Telegram
        answer = result.get("answer", "No pude obtener una respuesta.")
        await update.message.reply_text(answer)

    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("Hubo un error al conectar con el asistente.")

def main():
    # Configurar logging
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    # Crear la aplicación
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Comandos
    application.add_handler(CommandHandler("start", start))
    
    # Mensajes de texto
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Iniciar el bot
    print("El bot está corriendo...")
    application.run_polling()

if __name__ == '__main__':
    main()