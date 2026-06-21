// Конфигурация бота: список администраторов, чат техподдержки, категории техники.

const adminIds = (process.env.ADMIN_IDS || "")
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean)
  .map(Number)
  .filter((n) => Number.isInteger(n));

const supportChatId = process.env.SUPPORT_CHAT_ID
  ? Number(process.env.SUPPORT_CHAT_ID)
  : null;

const dbPath = process.env.DB_PATH || "./data/support.db";

// Категории обслуживаемой техники. Поле code попадает в БД, label — то, что видит пользователь.
const CATEGORIES = [
  { code: "computer", label: "💻 Компьютер / ноутбук" },
  { code: "printer", label: "🖨 Принтер / МФУ / сканер" },
  { code: "projector", label: "📽 Проектор / интерактивная доска" },
  { code: "network", label: "🌐 Сеть / интернет / Wi-Fi" },
  { code: "software", label: "🧩 Программное обеспечение" },
  { code: "other", label: "🔧 Другое" },
];

// Человекочитаемые названия статусов заявки.
const STATUS_LABELS = {
  new: "🆕 Новая",
  in_progress: "🛠 В работе",
  done: "✅ Выполнена",
  rejected: "🚫 Отклонена",
};

function categoryLabel(code) {
  const found = CATEGORIES.find((c) => c.code === code);
  return found ? found.label : code;
}

function isAdmin(userId) {
  return adminIds.includes(Number(userId));
}

module.exports = {
  adminIds,
  supportChatId,
  dbPath,
  CATEGORIES,
  STATUS_LABELS,
  categoryLabel,
  isAdmin,
};
