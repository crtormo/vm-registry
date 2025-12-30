import os
import httpx
import logging
import asyncio

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.enabled = bool(self.bot_token and self.chat_id)
        
        if not self.enabled:
            logger.warning("Telegram notifications disabled. TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing.")
        else:
            logger.info("Telegram notifications enabled.")

    async def send_message(self, message: str):
        """Envia un mensaje a Telegram"""
        if not self.enabled:
            return

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10.0)
                response.raise_for_status()
                logger.debug(f"Telegram message sent: {message}")
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")

    async def notify_new_device(self, ip, mac, hostname, vendor):
        msg = (
            f"🚨 *NUEVO DISPOSITIVO DETECTADO*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🌐 *IP:* `{ip}`\n"
            f"🏷️ *Host:* {hostname or 'Desconocido'}\n"
            f"🏭 *Vendor:* {vendor or 'N/A'}\n"
            f"🆔 *MAC:* `{mac}`"
        )
        await self.send_message(msg)

    async def notify_device_lost(self, ip, hostname="Desconocido"):
        msg = (
            f"👻 *DISPOSITIVO DESCONECTADO*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🌐 *IP:* `{ip}`\n"
            f"🏷️ *Host:* {hostname}"
        )
        await self.send_message(msg)

# Instancia global
notifier = TelegramNotifier()
