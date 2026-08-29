# Значки-логотипы активов у тикеров

Дата: 2026-08-29. Статус: набор и размещение одобрены пользователем по
макету в чате (вторая итерация: упрощённые НАСТОЯЩИЕ логотипы в гамме
сайта; COIN = «C» Coinbase).

## Идея и рамки

Напротив каждого тикера актива — одноцветный (currentColor, наследует
`--ice` #63f5a6 через CSS) упрощённый силуэт реального логотипа компании.
$GENOM значка не получает (наша монета). USDG — нейтральная «купюра»
(у стейбла нет знаменитой марки). Размещение: корзина консоли (sim и
live), лента-тикер лендинга, мини-корзина лендинга. Больше нигде.

Примечание: марки принадлежат владельцам; для локального демо приемлемо,
при публичном деплое учитывать брендбуки (зафиксировано в чате).

## Новый файл `icons.js`

Подключается `<script src="icons.js"></script>` в ОБОИХ html ПЕРЕД
front.js / app.js соответственно. Содержимое (финальные пути; при
браузерной шлифовке координатор может править ТОЛЬКО path-данные, чтобы
силуэт лучше читался, — структура и API неизменны):

```js
/* GENOM — ticker glyphs: simplified single-color marks, currentColor */
(function () {
  "use strict";
  var S = 'stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round"';
  var F = 'fill="currentColor"';
  var TKR_ICONS = {
    AAPL: '<g ' + F + '><path d="M16.6 12.9c0-2.2 1.8-3.2 1.9-3.3-1-1.5-2.6-1.7-3.2-1.7-1.4-.15-2.7.8-3.4.8-.7 0-1.8-.8-2.95-.77-1.51.02-2.9.87-3.68 2.22-1.57 2.72-.4 6.75 1.13 8.95.75 1.1 1.64 2.3 2.8 2.25 1.12-.05 1.55-.72 2.9-.72 1.34 0 1.74.72 2.92.69 1.21-.02 1.98-1.09 2.71-2.17.86-1.25 1.21-2.45 1.23-2.52-.03-.01-2.36-.91-2.36-3.73z"/><path d="M14.4 6.3c.6-.75 1.02-1.8.9-2.84-.88.04-1.98.6-2.62 1.34-.58.66-1.08 1.75-.94 2.76.99.08 2.01-.5 2.66-1.26z"/></g>',
    TSLA: '<g ' + S + ' stroke-width="2"><path d="M3.5 4.5C6.3 6.2 9 7 12 7s5.7-.8 8.5-2.5"/><path d="M12 7v14" stroke-width="2.6"/></g>',
    NVDA: '<g><path d="M2.5 12C6.5 5.8 12.5 4.2 21.5 4.8v14.4C12.5 19.8 6.5 18.2 2.5 12z" ' + S + ' stroke-width="1.6"/><path d="M8 12c2-3 5-3.8 8.2-3.4-2.6.9-4.4 2-5.2 3.4.8 1.4 2.6 2.5 5.2 3.4-3.2.4-6.2-.4-8.2-3.4z" ' + F + '/></g>',
    MSFT: '<g ' + F + '><rect x="4" y="4" width="7.4" height="7.4"/><rect x="12.6" y="4" width="7.4" height="7.4" opacity=".78"/><rect x="4" y="12.6" width="7.4" height="7.4" opacity=".78"/><rect x="12.6" y="12.6" width="7.4" height="7.4" opacity=".55"/></g>',
    AMZN: '<g ' + S + ' stroke-width="2"><path d="M4 10.5c2.6 2.8 5.2 4.2 8 4.2s5.4-1.4 8-4.4"/><path d="M20 10.3l-2.2-.35M20 10.3l-1.1 1.9"/><path d="M9.4 5.6c.4-1 1.4-1.6 2.6-1.6 1.6 0 2.6 1 2.6 2.6v3.1" stroke-width="1.7"/><path d="M14.6 7.4c-3.4.3-5.6 1.2-5.6 3 0 1.2.9 2 2.2 2 1.4 0 2.7-.9 3.4-2.3" stroke-width="1.7"/></g>',
    GOOGL: '<g ' + S + ' stroke-width="2.4"><path d="M19.6 12A7.6 7.6 0 1 1 17.1 6.3"/><path d="M12.6 12h7"/></g>',
    META: '<g ' + S + ' stroke-width="2.1"><path d="M4.2 15.6c0-5.6 2-8.9 4.3-8.9 3.4 0 4.6 10.6 7.6 10.6 1.9 0 3.7-2.3 3.7-5.4 0-3-1.5-5.2-3.3-5.2-2.9 0-4.6 10.6-7.9 10.6-2.1 0-4.4-1.7-4.4-1.7"/></g>',
    HOOD: '<g ' + S + ' stroke-width="1.7"><path d="M19.8 4.2c-6.3.3-11.6 4.2-13.6 9.9L4.5 19.5l5.6-1.9c5.6-2 9.3-7.2 9.7-13.4z"/><path d="M19.8 4.2C15 8.5 11 13 8.2 17.2"/></g>',
    COIN: '<path ' + F + ' d="M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zm0 13.8A4.8 4.8 0 1 1 12 7.2c2.35 0 4.3 1.7 4.72 3.9H11.2v1.8h5.52A4.81 4.81 0 0 1 12 16.8z"/>',
    PLTR: '<g><circle cx="12" cy="9.5" r="5.5" ' + F + ' opacity=".9"/><g ' + S + ' stroke-width="1.8"><path d="M4 15.5c2 2 5 3 8 3s6-1 8-3"/><path d="M5.5 19c1.8 1.3 4.1 2 6.5 2s4.7-.7 6.5-2"/></g></g>',
    USDG: '<g ' + S + ' stroke-width="1.7"><rect x="3" y="6" width="18" height="12" rx="2"/><circle cx="12" cy="12" r="3"/><path d="M6.5 9v6M17.5 9v6"/></g>'
  };
  window.tkrIcon = function (sym) {
    var body = TKR_ICONS[sym];
    if (!body) return "";
    return '<svg class="tkr-ico" viewBox="0 0 24 24" aria-hidden="true">' + body + "</svg>";
  };
})();
```

API: `window.tkrIcon(sym)` → строка `<svg class="tkr-ico">…</svg>` или ""
для неизвестного тикера (GENOM и любые будущие активы без значка — просто
пусто, ошибок нет).

## Точки вставки

1. app.js `renderBasket`: `'<div class="b-row"><span class="b-tkr">' + a +`
   → `'<div class="b-row"><span class="b-tkr">' + tkrIcon(a) + a +`
2. app.js `renderBasketLive`: `'<span class="b-tkr">' + esc(r.sym) + "</span>"`
   → `'<span class="b-tkr">' + tkrIcon(r.sym) + esc(r.sym) + "</span>"`
3. front.js `buildTape`: `'<span class="tape-item">' + a + " <b>"`
   → `'<span class="tape-item">' + tkrIcon(a) + a + " <b>"`
4. front.js `renderMini`: `'<div class="mb-row"><span class="mb-t">' + e[0] +`
   → `'<div class="mb-row"><span class="mb-t">' + tkrIcon(e[0]) + e[0] +`
5. console.html: `<script src="icons.js"></script>` строкой ПЕРЕД
   `<script src="app.js"></script>`.
6. index.html: `<script src="icons.js"></script>` строкой ПЕРЕД
   `<script src="front.js"></script>`.

## CSS

В app.css (рядом с `.b-tkr`):
```css
.tkr-ico { width: 13px; height: 13px; vertical-align: -2px; margin-right: 7px; opacity: .85; }
```
В front.css (лента и мини-корзина мельче):
```css
.tkr-ico { width: 12px; height: 12px; vertical-align: -2px; margin-right: 5px; opacity: .8; }
```

## Критерии приёмки

1. В корзине консоли у каждой из 10 акций и USDG — значок; сумма/проценты
   и бары не съехали. В live-корзине значки тоже появляются.
2. На лендинге значки в ленте и мини-корзине; $GENOM нигде значка не имеет
   (в ленте/корзине его и нет — карта просто не содержит GENOM).
3. `node --check` front.js, app.js, icons.js; тесты 46/46 (страховочно);
   ноль ошибок в консоли браузера.
4. Визуально (координатор): каждый силуэт читается как марка компании при
   13px; при необходимости координатор шлифует path-данные фикс-раундом.

## Вне объёма

Значки в деталях сделок track record, в guard-деталях и логе; цветные
версии логотипов; значок для $GENOM.
