# ДНК-метафоры в текстах Genom (лёгкое вплетение)

Дата: 2026-08-29. Статус: четыре конкретные правки одобрены пользователем
в чате дословно.

## Цель и рамки

Вплести ДНК-метафоры в тексты сайта, не теряя ни одного утверждения и не
уводя фокус с финансовой темы (агент/лимиты/индекс). Плотность — «легко»:
ровно четыре штриха на лендинге; консоль, бэкенд-тексты, цифры, футер,
worst case, rollout — не трогаются.

## Правки (index.html, точные строки «было → станет»)

1. Кикер hero:
   `$GENOM — A SELF-DRIVING INDEX TOKEN, BOXED IN BY HARD LIMITS`
   ⇒ `$GENOM — A SELF-DRIVING INDEX TOKEN WITH HARD LIMITS WRITTEN INTO ITS DNA`

2. Подзаголовок hero (второе предложение):
   `The weights are chosen by an autonomous agent.`
   ⇒ `The weights — the basket's genome — are chosen by an autonomous agent.`

3. Шаг 03 механики (первое предложение; формула дословно):
   `Before a single asset moves, the agent publishes keccak256(epoch, weights, thesis, nonce).`
   ⇒ `Before a single asset moves, the agent publishes keccak256(epoch, weights, thesis, nonce) — the decision's full genetic sequence.`

4. Шаг 04 механики (последнее предложение):
   `If any check fails, the epoch is voided and the basket does not move.`
   ⇒ `A vector that fails any check is a mutation that never replicates: the epoch is voided and the basket does not move.`

## Критерии приёмки

- Изменены ровно эти четыре текстовых узла index.html; больше ни одного
  байта нигде (включая meta description).
- Все прежние утверждения сохранены (self-driving/index/hard limits;
  автономный агент выбирает веса; формула keccak256 дословно; провал любой
  проверки → эпоха void, корзина не двигается).
- Лендинг открывается без ошибок; полный прогон тестов 46/46 (тексты
  лендинга тестами не проверяются — прогон страховочный).

## Вне объёма

Console.html, JS, server.py, README, любые новые секции или изменения
плотности метафор.
