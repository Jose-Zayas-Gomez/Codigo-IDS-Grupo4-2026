# Sem?foro IA

Aplicaci?n de escritorio en Python y PySide6 para registrar proyectos y modelos de IA, revisar costos e impacto ambiental y exportar informes. La persistencia local usa SQLite. Las integraciones con PostgreSQL, Ollama y MLflow requieren servicios configurados por separado.

## Ejecutar desde el c?digo

Requiere Python 3.13 x64. Crea un entorno virtual e instala las dependencias:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

La interfaz se inicia con `python main.py`. Consulta los comandos de la CLI con `python cli.py --help`. El servidor opcional se inicia con `python server_entry.py`.

## Contenido

- M?dulos de la interfaz, l?gica de negocio, persistencia, exportaciones e integraciones.
- `data/`: cat?logos y factores de referencia.
- `defaults/`: configuraci?n inicial sin cuentas ni credenciales.
- `locales/`: traducciones.
- `requirements.txt`: dependencias; `product.json`: informaci?n de versi?n.

## Descargas para Windows

El [instalador y el portable 1.0.2](https://github.com/Jose-Zayas-Gomez/Codigo-IDS-Grupo4-2026/releases/tag/v1.0.2) est?n disponibles como archivos adjuntos de la release, junto con sus checksums. Es una versi?n de prueba sin firma digital propia.

## Datos locales

La aplicaci?n guarda los datos de desarrollo en `userdata/`. La versi?n instalada utiliza `%LOCALAPPDATA%\SemaforoIA`; el portable utiliza `userdata/` junto a `portable.flag`. No subas configuraciones personales, credenciales, bases de datos, fotos de perfiles, respaldos ni exportaciones.
