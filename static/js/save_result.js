const saveForm = document.getElementById("save-result-form");
const saveStatus = document.getElementById("save-status");
let currentAttempt = 0;

function clearSaveStatus() {
    currentAttempt += 1;
    saveStatus.textContent = "";
}

async function saveResult(result) {
    const attempt = currentAttempt;
    saveStatus.textContent = "Збереження результату…";
    try {
        const response = await fetch(saveForm.action, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": saveForm.querySelector("[name=csrfmiddlewaretoken]").value,
            },
            body: JSON.stringify({ ...result, attempt_id: crypto.randomUUID() }),
        });
        const data = await response.json();
        if (!response.ok || !data.saved) throw new Error();
        if (attempt === currentAttempt) saveStatus.textContent = "Результат збережено.";
    } catch {
        if (attempt === currentAttempt) saveStatus.textContent = "Не вдалося зберегти результат.";
    }
}
