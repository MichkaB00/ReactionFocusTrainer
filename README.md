# Фокус

У цій лабораторній роботі додано аналіз результатів тренувань: статистику, графіки та порівняння за періодами.

Тренажер реакції та уваги зі статистикою і графіками результатів. Для аналізу використовуються NumPy, pandas і scikit-learn. Дані зберігаються в MongoDB. Для графіків потрібен інтернет.

## Запуск

Запустіть Docker Desktop і виконайте команди в папці проєкту:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
docker start focus-lab2-mongodb
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

Якщо контейнера MongoDB ще немає, створіть його замість команди `docker start`:

```powershell
docker run -d --name focus-lab2-mongodb -p 127.0.0.1:27017:27017 -v focus-lab2-mongodb-data:/data/db mongo:8
```

Сайт: [http://127.0.0.1:8000/](http://127.0.0.1:8000/). Статистика знаходиться в особистому кабінеті.

Для налаштованого запуску через WSL, Nginx і uWSGI: `.\start.cmd`. Сайт: [http://localhost:8080/](http://localhost:8080/).
