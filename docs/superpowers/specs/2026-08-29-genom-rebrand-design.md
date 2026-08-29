# Ребрендинг: Nostro Agent → Genom ($GENOM)

Дата: 2026-08-29. Статус: дизайн одобрен пользователем в чате (имя, тикер,
объём и знак S1 выбраны интерактивно).

## Решения пользователя

- Направление: ДНК-тематика; имя **Genom**, тикер **$GENOM** — оба без «E»,
  чтобы не смешиваться с GenomesDAO/GENOME (проверено: тикер GENOME занят).
- Объём: имя + тикер + сущности + CLI + **логотип**. Палитра, шрифты,
  вёрстка — без изменений.
- Знак: «S1 — чистая тонкая» — диагональная двойная спираль в тонком
  штрихе с перекладинами-штрихами; без точек-контактов и пунктира.
- Тексты остаются как после рерайта — меняются только бренд-токены.
  ДНК-метафоры в копирайт не вплетаются (отдельный проект при желании).

## 1. Карта переименований (везде: HTML, JS-строки, server.py, тесты, README)

| Было | Станет |
|---|---|
| Nostro Agent / NOSTRO AGENT | Genom Agent / GENOM AGENT |
| Nostro (отдельно) | Genom |
| $NSTRO | $GENOM |
| NSTRO (без $, как символ) | GENOM |
| `<title>Genom…`: «Nostro Agent — $NSTRO» | «Genom Agent — $GENOM» |
| «Nostro Console — $NSTRO local node» | «Genom Console — $GENOM local node» |
| Вордмарка `NOSTRO<em>CONSOLE</em>` | `GENOM<em>CONSOLE</em>` |
| NostroVault | GenomVault |
| NostroBasket | GenomBasket |
| NostroCommits | GenomCommits |
| «nostro fee vault» / «nostro basket» (live-теги) | «genom fee vault» / «genom basket» |
| CLI-файл `nstro` | `genom` (исполняемый, тот же shebang) |
| `./nstro connect|sim|status` (в текстах) | `./genom connect|sim|status` |
| `nstro.json` | `genom.json` (и в `.gitignore`) |
| Env `NSTRO_CONFIG` | `GENOM_CONFIG` (server.py и CLI) |
| HTTP `server_version` «NostroNode/0.1» | «GenomNode/0.1» |
| User-Agent «nstro-node/0.1» | «genom-node/0.1» |
| Docstring/принты сервера и CLI («Nostro node», «nostro node: http…», «nstro — switch…») | «Genom node», «genom node: http…», «genom — switch…» |
| README: бренд-строки | обновить на Genom/$GENOM и `./genom` |

Тесты обновляются синхронно: путь CLI в subprocess-тестах, `NSTRO_CONFIG` →
`GENOM_CONFIG`, проверка `b"NOSTRO"` на лендинге → `b"GENOM"`.

**Не меняется:** адрес fee vault, chain id 4663, DEFAULT_RPC, внешние URL
(blockscout, ponsfamily), имена холдеров симуляции, старые файлы в `docs/`
(исторические артефакты), папка проекта `~/nostro.capital` (переименование
пути — отдельное решение, вне объёма), палитра/шрифты/вёрстка.

## 2. Логотип (знак S1)

Все четыре носителя знака заменяются с куба на спираль; штриховой стиль
(stroke = currentColor, round caps/joins) сохраняется, цвета задаёт
существующий CSS.

Геометрия знака (вертикальная спираль, затем поворот −42° вокруг центра;
итоговый viewBox `0 0 240 240`, композиция отцентрована):

```svg
<g transform="rotate(-42 120 120) translate(20 5)">
  <g stroke="currentColor" stroke-width="8" fill="none"
     stroke-linecap="round" stroke-linejoin="round">
    <path d="M146 -4 C119 10 106 31 100 54 C52 89 52 137 100 172 C106 195 119 216 146 230"/>
    <path d="M54 -4 C81 10 94 31 100 54 C148 89 148 137 100 172 C94 195 81 216 54 230"/>
  </g>
  <g stroke="currentColor" stroke-width="6" fill="none" stroke-linecap="round">
    <path d="M95 11 L121 11"/><path d="M97 30 L110 30"/>
    <path d="M84 88 L120 88"/><path d="M80 113 L124 113"/><path d="M84 138 L116 138"/>
    <path d="M92 196 L105 196"/><path d="M81 215 L107 215"/>
  </g>
</g>
```

Носители и допустимая подгонка толщин (пропорции знака не меняются):

1. `index.html` — `.hd-mark` (шапка): strands stroke ≈ 14, rungs ≈ 11
   (толще базового, чтобы держать вес прежнего лого при 28px-высоте;
   финальная толщина подбирается визуально в браузере).
2. `index.html` — `.hero-ghost` (фоновый «призрак»): strands 6, rungs 4.5 —
   лёгкий контур, как у прежнего куба.
3. `console.html` — `.mark`: как `.hd-mark`.
4. `favicon.svg` — упрощённая версия: те же две нити, только 2 перекладины
   (средние `M84 88 L120 88` и `M84 138 L116 138` из среднего «глаза»),
   strands stroke ≈ 20, rungs ≈ 16 — иначе мельчит при 16px. Оформление —
   как в текущей фавиконке: viewBox `0 0 64 64`, подложка
   `<rect width="64" height="64" rx="14" fill="#050A12"/>`, знак штрихом
   `#ABE0FF` (масштабировать группу знака в поле 64×64 с полями ~7px).

`viewBox` всех инлайн-SVG меняется с `0 0 284 274` на `0 0 240 240`; CSS-
классы и размеры элементов не трогаются (знак почти квадратный, как куб).

## 3. Критерии приёмки

1. `grep -riE "nostro|nstro" --exclude-dir=docs --exclude-dir=.git .` из
   корня репо возвращает ноль строк (память/доки-артефакты вне репо не в
   счёт).
2. Полный прогон `python3 -m unittest tests.test_server -v` — 46/46;
   `node --check` обоих JS; `py_compile server.py`; `./genom status`
   работает против запущенного узла; `genom.json` создаётся CLI.
3. Браузер: обе страницы без JS-ошибок; в шапках — новый знак и
   GENOM-вордмарка; тикер $GENOM в ленте, кошельке, холдерах, логе;
   фавиконка-спираль видна на вкладке; hero-ghost — спираль. Скриншоты
   пользователю.
4. Логотип везде наследует цвет через currentColor (смена цвета CSS-ом
   меняет и знак) — проверить инспектором на одном носителе.

## Вне объёма

Переименование папки проекта и домена, смена палитры/шрифтов, ДНК-фразы в
текстах, обновление старых доков в `docs/`, деплой.
