# app.py
import os, sys, time, threading, atexit, webview, logging, traceback
from datetime import datetime
from multiprocessing import freeze_support

# ── PyInstaller helpers ──────────────────────────────────────────────────────
def resource_path(rel):
    """Resolve path đúng cả lúc dev lẫn sau khi đóng gói."""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


def unblock_bundled_files():
    """Remove Zone.Identifier ADS on bundled files (common when extracted from Downloads)."""
    if os.name != "nt":
        return

    base = getattr(sys, "_MEIPASS", None)
    if not base:
        return

    exts = {".dll", ".exe", ".pyd"}
    for root, _, files in os.walk(base):
        for name in files:
            if os.path.splitext(name)[1].lower() not in exts:
                continue
            path = os.path.join(root, name)
            try:
                os.remove(path + ":Zone.Identifier")
            except OSError:
                pass

# ── Import application modules ──────────────────────────────────────────────
from flask import Flask
from scheduler_instance import scheduler
from blueprints.FE_routes   import fe_bp
from blueprints.Run_Main   import main_run_bp
from blueprints.Run_Schedule import cron_bp, date_bp

logging.basicConfig(
    filename="app-debug.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s"
)
logging.info(
    "Scheduler timezone detected from this computer: %s (current time: %s)",
    scheduler.timezone,
    datetime.now(scheduler.timezone).isoformat(),
)

# ── Tạo Flask app ─────────────────────────────────────────────────────────────
app = Flask(
    __name__,
    template_folder=resource_path('templates'),
    static_folder=resource_path('static'),
)
app.secret_key = "tiktool-secret-change-me"

# ── Register blueprints ───────────────────────────────────────────────────────

app.register_blueprint(fe_bp)
app.register_blueprint(main_run_bp, url_prefix='/api')
app.register_blueprint(cron_bp, url_prefix='/cron') 
app.register_blueprint(date_bp, url_prefix='/date')


# ── Scheduler lifecycle ───────────────────────────────────────────────────────
# KHÔNG start scheduler ở đây — chỉ start khi user bấm /start
# Lý do: tránh spawn thread background khi multiprocessing fork child process

atexit.register(lambda: scheduler.shutdown(wait=False) if scheduler.running else None)

# ── Main ──────────────────────────────────────────────────────────────────────
def run_flask():
    app.run(
        host="127.0.0.1",
        port=2004,
        debug=True,
        use_reloader=False,
    )

if __name__ == "__main__":
    try:
        freeze_support()
        unblock_bundled_files()

        # Keep pythonnet on .NET Framework runtime for pywebview winforms backend.
        os.environ.setdefault("PYTHONNET_RUNTIME", "netfx")

        # Chạy Flask nền
        threading.Thread(target=run_flask, daemon=True).start()

        # Chờ Flask khởi động
        time.sleep(1)

        #Chạy WebView trên main thread
        webview.create_window(
            "IgTool",
            "http://127.0.0.1:2004",
            width=1200,
            height=800,
        )

        webview.start(gui='edgechromium')
    except Exception :
        logging.exception("crashed")

        with open("fatal-error.txt", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
  
