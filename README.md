# Фокус

## Що зроблено

Створено тренажер реакції на ESP32 у Wokwi. Результати передаються через MQTT і зберігаються в MongoDB для перегляду в Django.

## Як запустити

Запустіть Docker Desktop, потім у папці проєкту встановіть залежності та запустіть застосунок:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\start.cmd
```

`start.cmd` запускає наявний контейнер `focus-lab2-mongodb` та Django через налаштовані WSL, Nginx і uWSGI. Сайт: http://localhost:8080/. За потреби створіть обліковий запис на сайті.

В іншому вікні PowerShell знайдіть ID користувача й запустіть subscriber, підставивши його замість `1`:

```powershell
.\.venv\Scripts\python.exe manage.py shell -c "from django.contrib.auth.models import User; print(list(User.objects.values_list('id', 'username')))"
$env:FOCUS_MQTT_USER_ID = '1'
.\.venv\Scripts\python.exe mqtt_subscriber.py
```

Відкрийте https://wokwi.com/projects/new/esp32 і вставте в редактор вміст `wokwi/sketch.ino` та `wokwi/diagram.json`. У вкладці **Library Manager** натисніть **Add a new library**, знайдіть і виберіть **PubSubClient**. Wokwi створить файл `libraries.txt` із назвою бібліотеки.

Натисніть **Start Simulation** і дочекайтеся повідомлень `Wi-Fi connected.` та `MQTT connected.` у Serial Monitor. Підключення іноді займає більше 30 секунд. Потім натисніть кнопку, дочекайтесь зеленого світла і натисніть її ще раз. Оновіть особистий кабінет, щоб побачити результат в історії та статистиці.

Брокер `test.mosquitto.org` публічний, тому цей приклад призначений лише для навчання.
