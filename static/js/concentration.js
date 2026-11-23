const startButton = document.getElementById("start-button");
const responseButton = document.getElementById("response-button");
const signal = document.getElementById("signal");
const statusText = document.getElementById("status-text");
const progressText = document.getElementById("progress-text");
const summary = document.getElementById("summary");

let state = "idle";
let signals = [];
let completed = 0;
let correct = 0;
let falsePresses = 0;
let missed = 0;
let answered = false;
let deadline = 0;
let timer;
let frame;

function showStart() {
    responseButton.hidden = true;
    startButton.hidden = false;
    startButton.disabled = true;
    startButton.textContent = "Повторити";
    timer = setTimeout(() => {
        startButton.disabled = false;
        startButton.focus({ preventScroll: true });
    }, 350);
}

function finish() {
    state = "finished";
    signal.dataset.state = "idle";
    document.getElementById("correct-count").textContent = correct;
    document.getElementById("false-count").textContent = falsePresses;
    document.getElementById("missed-count").textContent = missed;
    summary.hidden = false;
    statusText.textContent = "Серію завершено";
    saveResult({
        mode: "concentration", correct_answers: correct,
        wrong_answers: falsePresses, missed_signals: missed,
    });
    showStart();
}

function endSignal() {
    if (state !== "signal") return;
    clearTimeout(timer);
    if (signals[completed] === "green") {
        if (answered) {
            correct += 1;
            statusText.textContent = "Правильно";
        } else {
            missed += 1;
            statusText.textContent = "Зелений сигнал пропущено";
        }
    } else if (answered) {
        falsePresses += 1;
        statusText.textContent = "Помилка: червоний сигнал";
    } else {
        correct += 1;
        statusText.textContent = "Правильно";
    }
    completed += 1;
    progressText.textContent = `Завершено: ${completed} / 10`;
    responseButton.disabled = true;
    signal.dataset.state = "idle";
    if (completed === signals.length) {
        finish();
    } else {
        scheduleSignal();
    }
}

function scheduleSignal() {
    state = "gap";
    timer = setTimeout(() => {
        frame = requestAnimationFrame(() => {
            answered = false;
            state = "signal";
            const color = signals[completed];
            signal.dataset.state = color;
            progressText.textContent = `Сигнал ${completed + 1} / 10`;
            statusText.textContent = color === "green" ? "Зелений — натисніть!" : "Червоний — не натискайте";
            responseButton.disabled = false;
            deadline = performance.now() + 1000;
            timer = setTimeout(endSignal, 1000);
        });
    }, 600);
}

function start() {
    if (state === "signal" || state === "gap") return;
    clearSaveStatus();
    signals = ["green", "green", "green", "green", "green", "red", "red", "red", "red", "red"];
    for (let i = signals.length - 1; i > 0; i -= 1) {
        const j = Math.floor(Math.random() * (i + 1));
        [signals[i], signals[j]] = [signals[j], signals[i]];
    }
    completed = 0;
    correct = 0;
    falsePresses = 0;
    missed = 0;
    progressText.textContent = "0 / 10";
    summary.hidden = true;
    startButton.hidden = true;
    responseButton.hidden = false;
    responseButton.disabled = true;
    signal.dataset.state = "idle";
    statusText.textContent = "Очікуйте сигналу";
    scheduleSignal();
}

function respond() {
    if (state !== "signal" || answered) return;
    // Перевіряємо строк відповіді, навіть якщо браузер затримав таймер.
    if (performance.now() >= deadline) {
        endSignal();
        return;
    }
    answered = true;
    responseButton.disabled = true;
}

function interrupt() {
    if (state !== "signal" && state !== "gap") return;
    clearTimeout(timer);
    cancelAnimationFrame(frame);
    state = "finished";
    signal.dataset.state = "idle";
    summary.hidden = true;
    statusText.textContent = "Серію перервано";
    showStart();
}

startButton.disabled = false;
startButton.addEventListener("click", (event) => {
    if (event.detail < 2) start();
});
responseButton.addEventListener("click", respond);
document.addEventListener("keydown", (event) => {
    if (event.code !== "Space" || event.isComposing) return;
    if (event.target.closest("a, input, textarea, select, button") !== responseButton
        && event.target !== document.body) return;
    if (state !== "signal" && state !== "gap") return;
    event.preventDefault();
    if (!event.repeat) respond();
});
document.addEventListener("visibilitychange", () => {
    if (document.hidden) interrupt();
});
window.addEventListener("pagehide", interrupt);
