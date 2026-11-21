const startButton = document.getElementById("start-button");
const responseButton = document.getElementById("response-button");
const signal = document.getElementById("signal");
const statusText = document.getElementById("status-text");

let state = "idle";
let timer;
let frame;
let startedAt = 0;

function finish(message) {
    clearTimeout(timer);
    cancelAnimationFrame(frame);
    state = "finished";
    signal.dataset.state = "idle";
    statusText.textContent = message;
    responseButton.hidden = true;
    startButton.hidden = false;
    startButton.disabled = true;
    startButton.textContent = "Повторити";
    // Коротка пауза захищає результат від подвійного натискання.
    timer = setTimeout(() => {
        startButton.disabled = false;
        startButton.focus({ preventScroll: true });
    }, 350);
}

function start() {
    if (state === "waiting" || state === "ready") return;
    clearSaveStatus();
    state = "waiting";
    startButton.hidden = true;
    responseButton.hidden = false;
    responseButton.focus({ preventScroll: true });
    signal.dataset.state = "waiting";
    statusText.textContent = "Очікуйте сигналу";
    timer = setTimeout(() => {
        frame = requestAnimationFrame(() => {
            signal.dataset.state = "green";
            statusText.textContent = "Натискайте!";
            startedAt = performance.now();
            state = "ready";
        });
    }, 1000 + Math.random() * 2000);
}

function respond() {
    if (state === "waiting") {
        finish("Зарано!");
    } else if (state === "ready") {
        const elapsed = Math.round(performance.now() - startedAt);
        finish(`${elapsed} мс`);
        saveResult({ mode: "reaction", reaction_time_ms: elapsed });
    }
}

startButton.disabled = false;
startButton.addEventListener("click", (event) => {
    if (event.detail < 2) start();
});
responseButton.addEventListener("click", (event) => {
    if (event.detail < 2) respond();
});
document.addEventListener("keydown", (event) => {
    if (event.code !== "Space" || event.isComposing) return;
    if (event.target.closest("a, input, textarea, select, button") !== responseButton
        && event.target !== document.body) return;
    if (state !== "waiting" && state !== "ready") return;
    event.preventDefault();
    if (!event.repeat) respond();
});
document.addEventListener("visibilitychange", () => {
    if (document.hidden && (state === "waiting" || state === "ready")) {
        finish("Спробу перервано");
    }
});
window.addEventListener("pagehide", () => {
    if (state === "waiting" || state === "ready") {
        finish("Спробу перервано");
    }
});
