# Heading Font Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Заменить шрифт заголовков Unbounded на Libre Franklin с подгонкой насыщенности, кегля и трекинга, чтобы сайт перестал читаться как шаблон «web3-стартап».

**Architecture:** Task 1 (исполнитель): токен `--fd` в двух CSS, шесть правил с новыми значениями, три ссылки на Google Fonts, правило `.code` в `404.html`. Task 2 (координатор): перерисовка `og.jpg`, браузерный проход на трёх ширинах, ревью, мерж, деплой.

**Tech Stack:** Статический HTML/CSS, Google Fonts. Проверка: набор из 58 тестов (`python3 -m unittest discover -s tests`), grep, браузер, прод-curl.

**Spec:** `docs/superpowers/specs/2026-08-31-heading-font-design.md`.

## Global Constraints

- Меняются ТОЛЬКО `front.css`, `app.css`, `index.html`, `console.html`, `404.html` + пересоздаётся `og.jpg` (Task 2). Никакие другие файлы не трогать.
- Не менять: цвета, фон, зелёную плашку `.hl`, моноширинный шрифт, `Inter` в основном тексте, тексты страниц, разметку блоков, `line-height` в изменяемых правилах.
- Семейства в ссылке `fonts.googleapis.com/css2` перечисляются по алфавиту.
- Сообщения коммитов заканчиваются строкой:
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`
- **Про подсчёты:** если в шаге указано ожидаемое число совпадений grep, а фактическое отличается — НЕ подгонять код под число. Сообщить фактический результат и объяснить расхождение.

---

### Task 1: Токен, шесть правил, три ссылки, страница 404

**Files:**
- Modify: `front.css:18`, `front.css:103-107`, `front.css:165-168`, `front.css:231-235`, `front.css:403`
- Modify: `app.css:16`, `app.css:195`, `app.css:228`
- Modify: `index.html:23`, `console.html:23`, `404.html:11`, `404.html:20-23`

**Interfaces:**
- Consumes: ничего (первая задача).
- Produces: CSS-переменную `--fd` со значением `"Libre Franklin", sans-serif` в `front.css` и `app.css`; Task 2 опирается на неё при перерисовке `og.jpg` (та же гарнитура, насыщенность 800).

- [ ] **Step 1: Токен `--fd` в `front.css`**

Строка 18. Заменить:

```css
  --fd: "Unbounded", sans-serif;
```

на:

```css
  --fd: "Libre Franklin", sans-serif;
```

- [ ] **Step 2: Токен `--fd` в `app.css`**

Строка 16. Точно та же замена, что в шаге 1:

```css
  --fd: "Unbounded", sans-serif;
```

на:

```css
  --fd: "Libre Franklin", sans-serif;
```

- [ ] **Step 3: Заголовок hero в `front.css`**

Заменить целиком правило (строки 103–107):

```css
.hero-in h1 {
  font-family: var(--fd); font-weight: 600;
  font-size: clamp(31px, 5vw, 66px); line-height: 1.1; letter-spacing: .01em;
  color: var(--ice-b); margin-bottom: 42px;
}
```

на:

```css
.hero-in h1 {
  font-family: var(--fd); font-weight: 800;
  font-size: clamp(29px, 4.6vw, 60px); line-height: 1.1; letter-spacing: -.016em;
  color: var(--ice-b); margin-bottom: 42px;
}
```

- [ ] **Step 4: Заголовки секций в `front.css`**

Заменить целиком правило (строки 165–168):

```css
.sec-head h2 {
  font-family: var(--fd); font-weight: 600; font-size: clamp(20px, 2.6vw, 34px);
  line-height: 1.22; letter-spacing: .01em; color: var(--ice-b);
}
```

на:

```css
.sec-head h2 {
  font-family: var(--fd); font-weight: 800; font-size: clamp(19px, 2.45vw, 32px);
  line-height: 1.22; letter-spacing: -.012em; color: var(--ice-b);
}
```

- [ ] **Step 5: Финальный заголовок в `front.css`**

Заменить целиком правило (строки 231–235):

```css
.fin h2 {
  font-family: var(--fd); font-weight: 600;
  font-size: clamp(24px, 3.6vw, 48px); line-height: 1.18; letter-spacing: .01em;
  color: var(--ice-b); margin-bottom: 44px; max-width: 900px;
}
```

на:

```css
.fin h2 {
  font-family: var(--fd); font-weight: 800;
  font-size: clamp(23px, 3.35vw, 45px); line-height: 1.18; letter-spacing: -.014em;
  color: var(--ice-b); margin-bottom: 44px; max-width: 900px;
}
```

- [ ] **Step 6: Числа в карточках лимитов, `front.css`**

Строка 403. Заменить:

```css
.gene-val { font-family: var(--fd); font-weight: 600; font-size: 22px; color: var(--ink); }
```

на:

```css
.gene-val { font-family: var(--fd); font-weight: 700; font-size: 22px; letter-spacing: -.01em; color: var(--ink); }
```

- [ ] **Step 7: Две цифры консоли в `app.css`**

Строка 195. Заменить:

```css
.w-stats div b { display: block; font-family: var(--fd); font-weight: 500; font-size: 20px; color: var(--ice); }
```

на:

```css
.w-stats div b { display: block; font-family: var(--fd); font-weight: 700; font-size: 20px; color: var(--ice); }
```

Строка 228. Заменить:

```css
.tr-run b { font-family: var(--fd); font-weight: 600; font-size: 34px; color: var(--ice); }
```

на:

```css
.tr-run b { font-family: var(--fd); font-weight: 700; font-size: 32px; letter-spacing: -.012em; color: var(--ice); }
```

- [ ] **Step 8: Ссылка на Google Fonts в `index.html`**

Строка 23. Заменить:

```html
<link href="https://fonts.googleapis.com/css2?family=Unbounded:wght@400;500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
```

на:

```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&family=Libre+Franklin:wght@700;800&display=swap" rel="stylesheet">
```

- [ ] **Step 9: Ссылка на Google Fonts в `console.html`**

Строка 23. Заменить:

```html
<link href="https://fonts.googleapis.com/css2?family=Unbounded:wght@400;500;600&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
```

на:

```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&family=Libre+Franklin:wght@700;800&display=swap" rel="stylesheet">
```

- [ ] **Step 10: Страница `404.html` — ссылка и правило `.code`**

Строка 11. Заменить:

```html
<link href="https://fonts.googleapis.com/css2?family=Unbounded:wght@600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

на:

```html
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Libre+Franklin:wght@800&display=swap" rel="stylesheet">
```

Строки 20–23. Заменить целиком правило:

```css
  .code {
    font-family: Unbounded, sans-serif; font-weight: 600; font-size: clamp(90px, 18vw, 160px);
    line-height: 1; color: transparent; -webkit-text-stroke: 2px rgba(99, 245, 166, .5);
  }
```

на:

```css
  .code {
    font-family: "Libre Franklin", sans-serif; font-weight: 800; font-size: clamp(84px, 16.5vw, 150px);
    line-height: 1; color: transparent; -webkit-text-stroke: 2px rgba(99, 245, 166, .5);
  }
```

- [ ] **Step 11: Проверка greps**

Выполнить и сообщить ФАКТИЧЕСКИЕ числа:

```bash
grep -rn "Unbounded" index.html console.html 404.html front.css app.css | wc -l
```

Ожидается `0`.

```bash
grep -c "Libre Franklin" front.css app.css 404.html
```

Ожидается по `1` на файл (`front.css:1`, `app.css:1`, `404.html:1`).

```bash
grep -c "Libre+Franklin" index.html console.html 404.html
```

Ожидается по `1` на файл.

```bash
grep -c "font-weight: 800" front.css
```

Ожидается `3` (hero h1, sec-head h2, fin h2).

Если любое число отличается — не править код под цифру, а сообщить факт и объяснить причину.

- [ ] **Step 12: Прогон тестов**

Run: `python3 -m unittest discover -s tests 2>&1 | tail -3`
Expected: `OK`, 58 тестов. Тесты покрывают симуляцию и не касаются CSS — это регрессионный страж, он должен остаться зелёным.

- [ ] **Step 13: Коммит**

```bash
git add front.css app.css index.html console.html 404.html
git commit -m "feat: шрифт заголовков Unbounded → Libre Franklin с подгонкой кегля и трекинга

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Координатор — og.jpg, браузерный проход, ревью, мерж, деплой

**Files:**
- Create: `og.jpg` (перезапись существующего, 1200×630)

**Interfaces:**
- Consumes: токен `--fd: "Libre Franklin", sans-serif` из Task 1; для canvas-отрисовки использовать `800 <size>px "Libre Franklin", sans-serif`.
- Produces: готовую к деплою ветку.

- [ ] Перерисовать `og.jpg`: canvas 1200×630 в браузере на странице с загруженным Libre Franklin (проверить `document.fonts.check('800 96px "Libre Franklin"')` перед отрисовкой). Композиция без изменений: фон `#020804` с радиальным градиентом, спираль справа, слово «GENOM» слева (Libre Franklin 800), гель-плашка «THE LIMITS ARE THE CONTRACT'S.» тёмным текстом, mono-строка «$GENOM · ROBINHOOD CHAIN · PONS V2». Вес до 200KB. Закоммитить отдельно.
- [ ] Браузерный проход на 375 / 1024 / 1440: заголовки не вылезают за края, горизонтальной прокрутки нет (`document.documentElement.scrollWidth <= window.innerWidth`), плашка `.hl` переносится корректно, `document.fonts.check('800 40px "Libre Franklin"')` → `true`, ноль ошибок консоли.
- [ ] Проверить `404.html` и консоль (`console.html`) — обе страницы на новом шрифте, цифры не слиплись.
- [ ] Ревью изменений; мерж по меню пользователя; пуш; деплой. Прод: `curl -s https://genom-iota.vercel.app/ | grep -c Libre+Franklin` → 1; `curl -sI https://genom-iota.vercel.app/og.jpg` → 200 image/jpeg.
