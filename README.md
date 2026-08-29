# Genom — локальный узел

Сайт Genom Agent ($GENOM): лендинг + консоль с полной симуляцией
экономики (эпохи, корзина, keccak-коммиты агента, MandateGuard, брейкер,
голосования) и live-режимом чтения Robinhood Chain.

## Запуск

    python3 server.py

Открыть http://localhost:8000 — лендинг, http://localhost:8000/console.html —
консоль. Python ≥ 3.9, зависимостей нет.

Флаги: `--port 8000`, `--seed N` (воспроизводимая симуляция), `--public`
(режим публичного узла — симуляция скрыта).

## Управление симуляцией

В шапке консоли: пауза, скорость эпохи (15/60/180 c), «next epoch».
Кнопки buy/sell/claim торгуют кошельком «you»; голосования — в карточке
Governance.

## Live-режим

    ./genom connect 0x<адрес-токена> [rpc-url]   # подключить контракт
    ./genom sim                                  # вернуть симуляцию
    ./genom status [порт]                        # что происходит

RPC по умолчанию: https://rpc.mainnet.chain.robinhood.com (chain id 4663).
Узел подхватывает genom.json на лету, рестарт не нужен.

## Тесты

    python3 -m unittest tests.test_server -v
