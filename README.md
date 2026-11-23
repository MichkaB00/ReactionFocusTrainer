# Фокус

Додано десять тестів Django для перевірки реєстрації, доступу до кабінету, збереження результатів і статистики.

## Запуск

У папці проєкту встановіть залежності:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Для запуску застосунку увімкніть Docker Desktop і виконайте:

```powershell
.\start.cmd
```

Потрібні наявний контейнер `focus-lab2-mongodb` і налаштовані WSL, Nginx та uWSGI. Сайт: http://localhost:8080/.

Для запуску тестів:

```powershell
.\.venv\Scripts\python.exe manage.py test
```

В активованому віртуальному середовищі можна виконати `python manage.py test`. Тести використовують тимчасову базу SQLite і не потребують запущеної MongoDB.
