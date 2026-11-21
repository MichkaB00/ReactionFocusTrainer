"""Підставляє локальні шляхи в конфігурацію Supervisor без зміни системи."""

import getpass
import os
from pathlib import Path
import secrets

if os.name != "posix":
    raise SystemExit("Виконайте цей файл у Linux/Ubuntu, а не у Windows.")

project_dir = Path(__file__).resolve().parent.parent
generated_dir = project_dir / "deploy" / "generated"
generated_dir.mkdir(mode=0o700, exist_ok=True)
(project_dir / "logs").mkdir(exist_ok=True)

secret_file = generated_dir / "secret-key"
if not secret_file.exists():
    secret_file.touch(mode=0o600)
    secret_file.write_text(secrets.token_hex(32), encoding="utf-8")

template = (project_dir / "deploy" / "supervisor.conf.example").read_text(encoding="utf-8")
config = template.replace("__PROJECT_DIR__", str(project_dir).replace("%", "%%"))
config = config.replace("__RUN_USER__", getpass.getuser())
config = config.replace("__SECRET_KEY__", secret_file.read_text(encoding="utf-8").strip())
config_file = generated_dir / "supervisor.conf"
config_file.touch(mode=0o600, exist_ok=True)
config_file.write_text(config, encoding="utf-8")
print(f"Підготовлено: {config_file}")
print("Системні конфігурації не змінено. Подальші команди наведені в README.md.")
