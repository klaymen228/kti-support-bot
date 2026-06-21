require("dotenv").config();

const { startBot } = require("./src/bot");

const token = process.env.BOT_TOKEN;

if (!token) {
  console.error(
    "Ошибка: не задан BOT_TOKEN. Скопируйте .env.example в .env и укажите токен бота от @BotFather."
  );
  process.exit(1);
}

startBot(token);

console.log("Бот техподдержки запущен. Ожидаю сообщения...");
