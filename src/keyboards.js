// Готовые клавиатуры (reply и inline) для интерфейса бота.

const { CATEGORIES, isAdmin } = require("./config");

// Главное меню (обычная клавиатура под полем ввода).
function mainMenu(userId) {
  const rows = [
    ["📝 Новая заявка"],
    ["📋 Мои заявки", "ℹ️ Помощь"],
  ];
  if (isAdmin(userId)) {
    rows.push(["🛠 Открытые заявки", "📊 Статистика"]);
  }
  return {
    reply_markup: {
      keyboard: rows,
      resize_keyboard: true,
    },
  };
}

// Inline-клавиатура выбора категории техники.
function categoryKeyboard() {
  const buttons = CATEGORIES.map((c) => [
    { text: c.label, callback_data: `cat:${c.code}` },
  ]);
  buttons.push([{ text: "❌ Отмена", callback_data: "cancel" }]);
  return { reply_markup: { inline_keyboard: buttons } };
}

// Кнопка отмены на шагах ввода текста.
const cancelKeyboard = {
  reply_markup: {
    inline_keyboard: [[{ text: "❌ Отмена", callback_data: "cancel" }]],
  },
};

// Подтверждение перед сохранением заявки.
const confirmKeyboard = {
  reply_markup: {
    inline_keyboard: [
      [
        { text: "✅ Отправить", callback_data: "confirm" },
        { text: "❌ Отмена", callback_data: "cancel" },
      ],
    ],
  },
};

// Кнопки для администратора под карточкой заявки.
function adminTicketKeyboard(ticket) {
  const rows = [];
  if (ticket.status === "new") {
    rows.push([
      { text: "🛠 Взять в работу", callback_data: `take:${ticket.id}` },
    ]);
  }
  if (ticket.status === "new" || ticket.status === "in_progress") {
    rows.push([
      { text: "✅ Выполнено", callback_data: `done:${ticket.id}` },
      { text: "🚫 Отклонить", callback_data: `reject:${ticket.id}` },
    ]);
  }
  return rows.length ? { reply_markup: { inline_keyboard: rows } } : {};
}

module.exports = {
  mainMenu,
  categoryKeyboard,
  cancelKeyboard,
  confirmKeyboard,
  adminTicketKeyboard,
};
