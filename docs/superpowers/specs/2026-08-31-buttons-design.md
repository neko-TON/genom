# Кнопки без рамок

Дата: 2026-08-31. Статус: дизайн одобрен пользователем.

## Задача

Пользователь: «сделай кнопки менее иишными». Диагноз — три признака
шаблона, по убыванию заметности:

1. **Стрелка после подписи** (`→`, `↗`, `↓`, `←`) — самая узнаваемая
   примета сгенерированного лендинга.
2. **Нет иерархии** — главная кнопка «перейти в консоль» оформлена ровно
   так же, как крошечная «COPY» рядом с адресом контракта: полая
   рамка-волосок, прозрачная заливка.
3. **Моноширинный капс с широкой разрядкой** (`.14em`) на кнопках — язык
   служебных надписей, а не действий.

Из трёх показанных вариантов (визуальный компаньон, экран `buttons.html`)
пользователь выбрал третий: кнопка перестаёт быть коробкой и превращается
в текст с толстым подчёркиванием.

Я рекомендовал второй вариант и предупредил, что третий проигрывает в
удобстве нажатия. Пользователь выбрал третий осознанно, поэтому в дизайн
включена отдельная защита области нажатия и её проверка в приёмке.

## Объём

### `front.css` — главная кнопка `.btn` (строки 122–128)

```css
.btn {
  display: inline-block; font-family: var(--fd); font-weight: 700; font-size: 15px;
  letter-spacing: -.006em; color: var(--ice);
  border: 0; border-bottom: 2px solid var(--ice); padding: 10px 0 8px; background: none;
  transition: color .2s, border-color .2s, transform .1s;
}
.btn:hover { color: var(--ice-b); border-color: var(--ice-b); }
.btn:active { transform: translateY(1px); }
```

Вертикальные отступы (`10px` / `8px`) сохранены намеренно: они держат
высоту области нажатия после потери рамки.

### `front.css` — второстепенная ссылка `.lnk` (строки 129–130)

```css
.lnk { font-family: var(--ft); font-size: 13px; color: var(--dim); border-bottom: 1px solid rgba(99, 245, 166, .2); padding-bottom: 2px; transition: color .2s, border-color .2s; }
.lnk:hover { color: var(--ice); border-color: var(--ice); }
```

Цвет поднят с `--mute` до `--dim` — без рамки подпись должна читаться
увереннее.

### `front.css` — кнопка копирования `#caCopy` (строки 361–367)

```css
#caCopy {
  flex: none; font-family: var(--fd); font-weight: 600; font-size: 11px;
  color: var(--ice); background: none; border: 0;
  border-bottom: 1px solid rgba(99, 245, 166, .5);
  padding: 0 0 3px; cursor: pointer; transition: color .2s, border-color .2s, transform .1s;
}
#caCopy:hover { color: var(--ice-b); border-color: var(--ice-b); }
#caCopy:active { transform: translateY(1px); }
```

В мобильном блоке (`@media (max-width: 760px)`, строка 372) правило
`#caCopy { padding: 9px 12px; }` удаляется — отступы больше не нужны,
область нажатия обеспечивается невидимым оверлеем.

### `front.css` — область нажатия (строки 345–349)

Существующий приём расширяется на две кнопки, потерявшие рамку:

```css
@media (max-width: 760px) {
  .lnk, .hd-console, .btn, #caCopy { position: relative; }
  .btn::after { content: ""; position: absolute; left: -6px; right: -6px; top: -10px; bottom: -10px; }
  .lnk::after, .hd-console::after, #caCopy::after { content: ""; position: absolute; left: -8px; right: -8px; top: -15px; bottom: -15px; }
}
```

Оверлей разделён на два правила. У `.btn` своя высота уже есть за счёт
вертикальных отступов, ей хватает прежнего запаса в 10px. У остальных трёх
подписи мелкие (11–13px), и прежний запас давал около 37px — меньше
требуемых 44px. Поэтому для них запас поднят до 15px: это касается и
`.lnk` с `.hd-console`, у которых зона нажатия недотягивала до нормы ещё
до этой правки.

### `index.html` — подписи и классы

| Строка | Было | Стало |
|---|---|---|
| 58 | `<a class="hd-console mono" href="console.html">LAUNCH CONSOLE ↗</a>` | `<a class="hd-console mono" href="console.html">LAUNCH CONSOLE</a>` |
| 82 | `<a class="btn mono" href="console.html">GO TO THE LIVE CONSOLE&nbsp;→</a>` | `<a class="btn" href="console.html">Go to the live console</a>` |
| 83 | `<a class="lnk mono" href="index.html#how">see how it runs ↓</a>` | `<a class="lnk" href="index.html#how">see how it runs</a>` |
| 89 | `…aria-label="Copy contract address">COPY</button>` | `…aria-label="Copy contract address">Copy</button>` |
| 271 | `<a class="btn mono" href="console.html">STEP INTO THE CONSOLE&nbsp;→</a>` | `<a class="btn" href="console.html">Step into the console</a>` |
| 324 | `<a class="btn mono" href="console.html">GO TO THE LIVE CONSOLE&nbsp;→</a>` | `<a class="btn" href="console.html">Go to the live console</a>` |

Класс `mono` снимается с `.btn` и `.lnk`, чтобы шрифт задавался одним
правилом, а не порядком следования в файле. У `.hd-console` он остаётся:
ссылка в шапке набрана заодно с логотипом и меню, менять только её значит
рассогласовать шапку. `aria-label` кнопки копирования не меняется.

### `404.html`

Правило `.back` (строки 29–36):

```css
  .back {
    display: inline-block; margin-top: 34px; padding: 10px 0 8px;
    font-family: "Libre Franklin", sans-serif; font-weight: 700; font-size: 15px;
    letter-spacing: -.006em; color: #63f5a6; text-decoration: none;
    border: 0; border-bottom: 2px solid #63f5a6; background: none;
    transition: color .2s, border-color .2s, transform .1s;
  }
  .back:hover { color: #c9ffdf; border-color: #c9ffdf; }
  .back:active { transform: translateY(1px); }
```

Подпись: `← BACK TO THE GENOME` → `Back to the genome`.

Ссылка на шрифты (строка 11) должна запросить вес 700, который появляется
у `.back`, иначе браузер подделает жирное начертание:

```html
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Libre+Franklin:wght@700;800&display=swap" rel="stylesheet">
```

## Критерии приёмки

1. В подписях кнопок и ссылок нет глифов `→`, `↗`, `↓`, `←`. Проверка
   счётом: `grep -c '→\|↗\|↓\|←' index.html` → **3**, `… 404.html` → **0**.
   Три оставшихся в `index.html` — не кнопки и вне объёма: строка 18
   (мета-описание для Twitter), строки 180 и 200 (тексты карточек
   механики «Bonding curve → Uniswap v4» и «Fail one → epoch voided»).
2. У `.btn`, `.lnk`, `#caCopy`, `.back` нет рамки-коробки и фона:
   `border-width` по сторонам, кроме нижней, равен нулю, `background`
   прозрачен.
3. На ширине 375px высота области нажатия каждой из `.btn`, `.lnk`,
   `#caCopy`, `.hd-console` — не меньше 44px. Замер: к
   `el.getBoundingClientRect().height` прибавить модули значений `top` и
   `bottom`, прочитанных из `getComputedStyle(el, '::after')` (сам
   псевдоэлемент через `getBoundingClientRect()` не измеряется).
4. `document.fonts.check('700 15px "Libre Franklin"')` истинно на главной
   и на 404.
5. Тесты 58/58, ноль ошибок консоли, горизонтальной прокрутки нет на
   375 / 1024 / 1440.
6. `app.css` не изменён — кнопки консоли остаются с рамками.

## Вне объёма

Цвета, фон, заголовки, тексты страниц, разметка блоков, картинка для
шеринга.

**Кнопки консоли (`app.css`, `.ctl`) сознательно не трогаем:** на проде
они скрыты режимом наблюдателя, среди них есть выпадающий список скорости,
которому рамка нужна как опознавательный знак, и панель управления — иной
жанр интерфейса, чем призыв к действию на лендинге.
