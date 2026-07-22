# 🪟 Установка Player Agent на Windows 10/11

Пошаговая инструкция для ноутбука у звуковой системы лагеря.

## 1. Установить Python
Скачайте Python 3.11+ с <https://www.python.org/downloads/>. При установке
поставьте галочку **«Add python.exe to PATH»**. Проверка:
```powershell
python --version
```

## 2. Установить mpv
Скачайте сборку для Windows с <https://mpv.io/installation/> (раздел Windows).
Распакуйте `mpv.exe`, например в `C:\mpv\`. Либо добавьте папку в `PATH`, либо
позже укажите путь в `.env` (`MPV_EXECUTABLE_PATH=C:\mpv\mpv.exe`).

## 3. Проверить путь к mpv
```powershell
mpv --version        # если в PATH
# или
C:\mpv\mpv.exe --version
```

## 4. Подключить USB-аудиоинтерфейс
Подключите звуковую карту/интерфейс к ноутбуку и к микшеру/усилителю. Дождитесь
установки драйверов Windows.

## 5. Получить список аудиоустройств
```powershell
git clone <repo> living-water
cd living-water
.\scripts\windows\install.ps1
.\scripts\windows\status.ps1 -Audio
```
Вы увидите список вида `wasapi/{...}  (USB Audio Interface)`.

## 6. Выбрать нужное устройство
Скопируйте имя нужного устройства в `.env`:
```ini
MPV_AUDIO_DEVICE=wasapi/{0.0.0.00000000}.{...}
```
Пустое значение = устройство Windows по умолчанию.

## 7. Заполнить .env
```ini
AGENT_SERVER_URL=wss://camp.example.org/ws/agent   # или ws://127.0.0.1:8000/ws/agent для LOCAL_MVP
AGENT_API_BASE_URL=https://camp.example.org        # или http://127.0.0.1:8000
AGENT_DEVICE_ID=main-camp-speakers
AGENT_DEVICE_TOKEN=<секрет устройства>
MPV_EXECUTABLE_PATH=C:\mpv\mpv.exe
MPV_AUDIO_DEVICE=<из шага 6>
RESUME_AFTER_RESTART=false
```

## 8. Запустить тестовый звук
```powershell
cd apps\player-agent
..\..\.venv\Scripts\python -m agent.cli test-audio
```
Вы должны услышать короткий тон в рупорах.

## 9. Установить в автозапуск
```powershell
.\scripts\windows\register-startup-task.ps1
Start-ScheduledTask -TaskName LivingWaterPlayerAgent
```
Отключите сон Windows, чтобы звук не прерывался:
```powershell
powercfg /change standby-timeout-ac 0
powercfg /change monitor-timeout-ac 0
```

## 10. Проверить аварийную остановку
```powershell
.\scripts\windows\stop.ps1     # звук должен немедленно прекратиться
```

## Управление
| Действие | Команда |
|---|---|
| Запуск (вручную) | `.\scripts\windows\start.ps1` |
| Статус | `.\scripts\windows\status.ps1` |
| Аварийный стоп | `.\scripts\windows\stop.ps1` |
| Убрать автозапуск | `.\scripts\windows\unregister-startup-task.ps1` |
