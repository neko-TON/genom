# Пакет «Люкс»: шаринг-превью, 404, микрофизика

Дата: 2026-08-30. Статус: дизайн одобрен пользователем.

## 1. Шаринг-превью (OG/Twitter)

- Ассет `og.jpg` 1200×630 (генерируется координатором через canvas в
  браузере с реальными шрифтами сайта; ~<200KB): тёмный лаб-фон #020804 с
  лёгким радиальным градиентом, стилизованная спираль справа (тонкие
  синусоиды в гель-зелёном), слева — «GENOM» (Unbounded), строка-плашка
  «THE LIMITS ARE THE CONTRACT'S.» (гель-плашка, тёмный текст), mono-строка
  «$GENOM · ROBINHOOD CHAIN · PONS V2». Кладётся в корень репо (статика
  Vercel).
- index.html head: og:title («Genom Agent — $GENOM»), og:description
  (существующий description), og:image (абсолютный
  https://genom-iota.vercel.app/og.jpg), og:type website, og:url,
  twitter:card summary_large_image + twitter:title/description/image.
- console.html head: meta description («Live observer console of the
  Genom node: basket, NAV curve, sealed decisions and the mandate guard.»)
  + тот же набор OG/Twitter с og:title «Genom Console — $GENOM».
- Обе страницы: `<meta name="theme-color" content="#020804">`.

## 2. Страница 404

- `404.html` в корне (Vercel отдаёт её автоматически для не найденных
  путей; локальный server.py не меняется — его 404 остаётся JSON, это ок).
- Стиль сайта: тёмный фон, mono; крупно «404», строка
  «GENE NOT FOUND» с мигающей кареткой (CSS в самом файле, без внешних
  зависимостей кроме Google Fonts), короткая строка
  «This sequence does not exist in the genome.» и ссылка-кнопка
  «← BACK TO THE GENOME» на «/». Reduced-motion: каретка статична.
  theme-color, favicon, noindex не нужен (404 сама по себе).

## 3. Микрофизика

- front.css: `.btn:active { transform: translateY(1px); }` (+ transition
  transform .1s добавить к существующему transition); `#caCopy:active`
  так же; `.gene:hover, .mcard:hover { border-color: var(--line-2);
  background: rgba(99, 245, 166, .05); }` с transition (лёгкое «оживание»
  карточек, без подъёма — тихий стиль сохраняем; текущий border уже
  --line-2 → ховер меняет только фон… уточнение: базовый бордер карточек
  сейчас var(--line-2); ховер — background .03→.06 и border до
  rgba(99,245,166,.4)); всё без движения → reduced-motion не требуется,
  но transition указывается.
- app.css: `.ctl:active { transform: translateY(1px); }` + transition.

## Критерии приёмки

1. Валидные OG-меты на обеих страницах (проверка: curl + grep, визуально
   og.jpg открывается и выглядит по описанию); превью-карточка
   разворачивается в Telegram/Twitter-валидаторе (проверка внешним
   валидатором вне объёма — достаточно корректных тегов и доступного
   изображения).
2. https://genom-iota.vercel.app/nesuschestvuet → фирменная 404.
3. Кнопки «вдавливаются» при клике, карточки оживают при ховере; ноль
   ошибок консоли; тесты 58/58; мерж и деплой по подтверждению.

## Вне объёма

Кастомный домен, sitemap/robots, аналитика, изменение текстов и блоков.
