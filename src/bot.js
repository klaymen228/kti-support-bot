// Основная логика Telegram-бота техподдержки.

const TelegramBot = require("node-telegram-bot-api");

const { adminIds, supportChatId, isAdmin, categoryLabel, STATUS_LABELS } =
  require("./config");
const tickets = require("./tickets");
const kb = require("./keyboards");

// Состояние диалога каждого пользователя (шаги создания заявки и т.п.).
// Для учебного проекта/одного процесса достаточно хранения в памяти.
const sessions = new Map();

function escapeHtml(text) {
  return String(text ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function userMention(ticket) {
  const name = ticket.contact_name || ticket.username || `id ${ticket.user_id}`;
  const handle = ticket.username ? ` (@${ticket.username})` : "";
  return escapeHtml(name) + handle;
}

// Карточка заявки. forAdmin добавляет служебные данные (автор, контакт).
function formatTicket(ticket, { forAdmin = false } = {}) {
  const lines = [
    `<b>Заявка #${ticket.id}</b>  ${STATUS_LABELS[ticket.status] || ticket.status}`,
    `📂 Категория: ${escapeHtml(categoryLabel(ticket.category))}`,
    `📍 Где: ${escapeHtml(ticket.location)}`,
    `📝 Проблема: ${escapeHtml(ticket.description)}`,
  ];
  if (forAdmin) {
    lines.push(`👤 Автор: ${userMention(ticket)}`);
  }
  lines.push(`🕒 Создана: ${escapeHtml(ticket.created_at)} UTC`);
  return lines.join("\n");
}

function startBot(token) {
  const bot = new TelegramBot(token, { polling: true });

  bot.on("polling_error", (err) => {
    console.error("Ошибка polling:", err.message);
  });

  // Оповестить администраторов (и рабочий чат) о новой заявке.
  async function notifyAdmins(ticket) {
    const text = "🔔 <b>Новая заявка</b>\n\n" + formatTicket(ticket, { forAdmin: true });
    const opts = { parse_mode: "HTML", ...kb.adminTicketKeyboard(ticket) };

    for (const adminId of adminIds) {
      try {
        await bot.sendMessage(adminId, text, opts);
      } catch (e) {
        // Админ ещё не открыл диалог с ботом — пропускаем.
      }
    }
    if (supportChatId) {
      try {
        await bot.sendMessage(supportChatId, text, opts);
      } catch (e) {
        console.error("Не удалось отправить в чат техподдержки:", e.message);
      }
    }
  }

  // Сообщить автору об изменении статуса его заявки.
  async function notifyAuthor(ticket, extra = "") {
    const text =
      `Статус вашей заявки #${ticket.id} изменён: ${STATUS_LABELS[ticket.status]}` +
      (extra ? `\n\n${escapeHtml(extra)}` : "");
    try {
      await bot.sendMessage(ticket.user_id, text, { parse_mode: "HTML" });
    } catch (e) {
      // ignore
    }
  }

  function sendMainMenu(chatId, userId, text) {
    return bot.sendMessage(chatId, text, {
      parse_mode: "HTML",
      ...kb.mainMenu(userId),
    });
  }

  // ===== Команды =====

  bot.onText(/^\/start$/, (msg) => {
    sessions.delete(msg.from.id);
    const greeting =
      "👋 Здравствуйте! Это бот техподдержки колледжа.\n\n" +
      "Здесь можно оставить заявку на ремонт или обслуживание техники " +
      "(компьютеры, принтеры, проекторы, сеть и т.д.).\n\n" +
      "Нажмите <b>«📝 Новая заявка»</b>, чтобы начать.";
    sendMainMenu(msg.chat.id, msg.from.id, greeting);
  });

  bot.onText(/^\/help$/, (msg) => sendHelp(msg.chat.id, msg.from.id));

  bot.onText(/^\/cancel$/, (msg) => {
    sessions.delete(msg.from.id);
    sendMainMenu(msg.chat.id, msg.from.id, "Действие отменено.");
  });

  bot.onText(/^\/myrequests$/, (msg) =>
    showUserTickets(msg.chat.id, msg.from.id)
  );

  // ===== Обработка обычных сообщений =====

  bot.on("message", async (msg) => {
    if (!msg.text || msg.text.startsWith("/")) return; // команды обрабатываются выше

    const userId = msg.from.id;
    const chatId = msg.chat.id;
    const text = msg.text.trim();

    // Кнопки главного меню
    switch (text) {
      case "📝 Новая заявка":
        return beginNewTicket(chatId, userId);
      case "📋 Мои заявки":
        return showUserTickets(chatId, userId);
      case "ℹ️ Помощь":
        return sendHelp(chatId, userId);
      case "🛠 Открытые заявки":
        if (isAdmin(userId)) return showActiveTickets(chatId, userId);
        break;
      case "📊 Статистика":
        if (isAdmin(userId)) return showStats(chatId, userId);
        break;
    }

    // Шаги диалога
    const session = sessions.get(userId);
    if (!session) {
      return sendMainMenu(
        chatId,
        userId,
        "Не понял команду. Воспользуйтесь кнопками меню ниже."
      );
    }

    if (session.step === "location") {
      session.draft.location = text;
      session.step = "description";
      return bot.sendMessage(
        chatId,
        "📝 Опишите проблему: что именно не работает?",
        kb.cancelKeyboard
      );
    }

    if (session.step === "description") {
      session.draft.description = text;
      session.step = "contact";
      return bot.sendMessage(
        chatId,
        "👤 Укажите контакт для связи: ФИО и/или телефон.\n" +
          "Или нажмите «Пропустить», чтобы использовать ваше имя в Telegram.",
        {
          reply_markup: {
            inline_keyboard: [
              [{ text: "Пропустить", callback_data: "skip_contact" }],
              [{ text: "❌ Отмена", callback_data: "cancel" }],
            ],
          },
        }
      );
    }

    if (session.step === "contact") {
      session.draft.contactName = text;
      return showConfirmation(chatId, userId);
    }

    if (session.step === "reject_reason") {
      return finishReject(chatId, userId, session, text);
    }
  });

  // ===== Обработка inline-кнопок =====

  bot.on("callback_query", async (query) => {
    const userId = query.from.id;
    const chatId = query.message.chat.id;
    const data = query.data || "";
    const [action, arg] = data.split(":");

    const ack = (text) => bot.answerCallbackQuery(query.id, { text }).catch(() => {});

    if (action === "cancel") {
      sessions.delete(userId);
      await ack("Отменено");
      return sendMainMenu(chatId, userId, "Действие отменено.");
    }

    if (action === "cat") {
      const session = sessions.get(userId);
      if (!session || session.step !== "category") return ack();
      session.draft.category = arg;
      session.step = "location";
      await ack();
      return bot.sendMessage(
        chatId,
        "📍 Укажите расположение техники: корпус, этаж, кабинет/аудитория.\n" +
          "Например: «Корпус А, ауд. 214».",
        kb.cancelKeyboard
      );
    }

    if (action === "skip_contact") {
      const session = sessions.get(userId);
      if (!session || session.step !== "contact") return ack();
      const tgName = [query.from.first_name, query.from.last_name]
        .filter(Boolean)
        .join(" ");
      session.draft.contactName = tgName || query.from.username || "";
      await ack();
      return showConfirmation(chatId, userId);
    }

    if (action === "confirm") {
      const session = sessions.get(userId);
      if (!session || session.step !== "confirm") return ack();
      const ticket = tickets.createTicket({
        userId,
        username: query.from.username,
        ...session.draft,
      });
      sessions.delete(userId);
      await ack("Заявка отправлена");
      await bot.editMessageReplyMarkup(
        { inline_keyboard: [] },
        { chat_id: chatId, message_id: query.message.message_id }
      ).catch(() => {});
      await sendMainMenu(
        chatId,
        userId,
        `✅ Заявка <b>#${ticket.id}</b> принята! Сотрудник техподдержки свяжется с вами.\n` +
          `Отслеживать статус можно в разделе «📋 Мои заявки».`
      );
      return notifyAdmins(ticket);
    }

    // --- Действия администратора ---
    if (["take", "done", "reject"].includes(action)) {
      if (!isAdmin(userId)) return ack("Недостаточно прав");
      const ticket = tickets.getTicket(Number(arg));
      if (!ticket) return ack("Заявка не найдена");

      if (action === "take") {
        const updated = tickets.updateStatus(ticket.id, "in_progress", userId);
        await ack("Взято в работу");
        await refreshAdminCard(chatId, query.message.message_id, updated);
        return notifyAuthor(updated, "Специалист приступил к выполнению.");
      }

      if (action === "done") {
        const updated = tickets.updateStatus(ticket.id, "done", userId);
        await ack("Заявка закрыта");
        await refreshAdminCard(chatId, query.message.message_id, updated);
        return notifyAuthor(updated, "Работы выполнены. Спасибо за обращение!");
      }

      if (action === "reject") {
        // Запрашиваем причину отклонения отдельным сообщением.
        sessions.set(userId, {
          step: "reject_reason",
          rejectTicketId: ticket.id,
          rejectMessage: { chatId, messageId: query.message.message_id },
        });
        await ack();
        return bot.sendMessage(
          chatId,
          `Укажите причину отклонения заявки #${ticket.id}:`,
          kb.cancelKeyboard
        );
      }
    }

    return ack();
  });

  // ===== Вспомогательные функции диалога =====

  function beginNewTicket(chatId, userId) {
    sessions.set(userId, { step: "category", draft: {} });
    return bot.sendMessage(
      chatId,
      "Выберите категорию техники:",
      kb.categoryKeyboard()
    );
  }

  function showConfirmation(chatId, userId) {
    const session = sessions.get(userId);
    session.step = "confirm";
    const d = session.draft;
    const preview =
      "Проверьте заявку перед отправкой:\n\n" +
      `📂 Категория: ${escapeHtml(categoryLabel(d.category))}\n` +
      `📍 Где: ${escapeHtml(d.location)}\n` +
      `📝 Проблема: ${escapeHtml(d.description)}\n` +
      `👤 Контакт: ${escapeHtml(d.contactName || "—")}`;
    return bot.sendMessage(chatId, preview, {
      parse_mode: "HTML",
      ...kb.confirmKeyboard,
    });
  }

  async function finishReject(chatId, userId, session, reason) {
    const ticket = tickets.getTicket(session.rejectTicketId);
    sessions.delete(userId);
    if (!ticket) {
      return sendMainMenu(chatId, userId, "Заявка не найдена.");
    }
    tickets.addComment(ticket.id, userId, `Отклонено: ${reason}`);
    const updated = tickets.updateStatus(ticket.id, "rejected", userId);
    if (session.rejectMessage) {
      await refreshAdminCard(
        session.rejectMessage.chatId,
        session.rejectMessage.messageId,
        updated
      );
    }
    await notifyAuthor(updated, `Причина: ${reason}`);
    return sendMainMenu(chatId, userId, `Заявка #${ticket.id} отклонена.`);
  }

  async function refreshAdminCard(chatId, messageId, ticket) {
    const text = "🔔 <b>Заявка</b>\n\n" + formatTicket(ticket, { forAdmin: true });
    await bot
      .editMessageText(text, {
        chat_id: chatId,
        message_id: messageId,
        parse_mode: "HTML",
        ...kb.adminTicketKeyboard(ticket),
      })
      .catch(() => {});
  }

  function showUserTickets(chatId, userId) {
    const list = tickets.getUserTickets(userId);
    if (!list.length) {
      return sendMainMenu(
        chatId,
        userId,
        "У вас пока нет заявок. Нажмите «📝 Новая заявка», чтобы создать."
      );
    }
    const text = list.map((t) => formatTicket(t)).join("\n\n");
    return bot.sendMessage(chatId, text, { parse_mode: "HTML" });
  }

  async function showActiveTickets(chatId, userId) {
    const list = tickets.getActiveTickets();
    if (!list.length) {
      return bot.sendMessage(chatId, "🎉 Открытых заявок нет.");
    }
    await bot.sendMessage(chatId, `Открытых заявок: ${list.length}`);
    for (const t of list) {
      await bot.sendMessage(chatId, formatTicket(t, { forAdmin: true }), {
        parse_mode: "HTML",
        ...kb.adminTicketKeyboard(t),
      });
    }
  }

  function showStats(chatId, userId) {
    const s = tickets.getStats();
    const text =
      "📊 <b>Статистика заявок</b>\n\n" +
      `${STATUS_LABELS.new}: ${s.new}\n` +
      `${STATUS_LABELS.in_progress}: ${s.in_progress}\n` +
      `${STATUS_LABELS.done}: ${s.done}\n` +
      `${STATUS_LABELS.rejected}: ${s.rejected}\n` +
      `\nВсего: ${s.total}`;
    return bot.sendMessage(chatId, text, { parse_mode: "HTML" });
  }

  function sendHelp(chatId, userId) {
    const lines = [
      "<b>ℹ️ Помощь</b>",
      "",
      "Бот принимает заявки на обслуживание техники колледжа.",
      "",
      "• <b>📝 Новая заявка</b> — создать обращение (категория → место → описание → контакт).",
      "• <b>📋 Мои заявки</b> — посмотреть статусы своих обращений.",
      "• /cancel — прервать создание заявки.",
    ];
    if (isAdmin(userId)) {
      lines.push(
        "",
        "<b>Для техподдержки:</b>",
        "• <b>🛠 Открытые заявки</b> — список новых и заявок в работе с кнопками управления.",
        "• <b>📊 Статистика</b> — сводка по статусам.",
        "• Кнопки под заявкой: взять в работу, выполнено, отклонить."
      );
    }
    return bot.sendMessage(chatId, lines.join("\n"), { parse_mode: "HTML" });
  }

  return bot;
}

module.exports = { startBot };
