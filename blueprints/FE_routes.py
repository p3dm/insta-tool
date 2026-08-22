import os, time, threading, webbrowser
from flask import Blueprint, render_template, request, jsonify, redirect
from werkzeug.utils import secure_filename

from scheduler_instance import scheduler

from config import (
    load_config, save_config,
    parse_spreadsheet_id, USER_DATA_DIR
)
# from scheduler_instance import scheduler

# Import process registry để stop_all có thể kill tất cả
from blueprints.Run_Main import _process_lock, _active_processes

fe_bp = Blueprint('fe_bp', __name__)

# ── Routes ────────────────────────────────────────────────────────────────────

@fe_bp.route('/')
def index():
    cfg = load_config()
    return render_template('index.html', config=cfg)


@fe_bp.route('/schedule-jobs')
def schedule_jobs():
    """Trang quản lý các job đang được APScheduler giữ trong bộ nhớ."""
    return render_template('list_schedule.html')


@fe_bp.route('/save-config', methods=['POST'])
def save_config_route():
    cfg       = load_config()
    sheet_url = request.form.get("sheet_url", "").strip()
    json_file = request.files.get("service_account")

    errors = {}

    # Validate sheet URL
    if sheet_url:
        sid = parse_spreadsheet_id(sheet_url)
        if not sid:
            errors["sheet_url"] = "URL Google Sheet không hợp lệ."
        else:
            cfg["sheet_url"]      = sheet_url
            cfg["spreadsheet_id"] = sid
    else:
        errors["sheet_url"] = "Vui lòng nhập URL Google Sheet."

    # Validate + lưu service account JSON
    if json_file and json_file.filename.endswith('.json'):
        filename  = secure_filename(json_file.filename)
        dest_path = os.path.join(USER_DATA_DIR, filename)
        json_file.save(dest_path)

        try:
            from google.oauth2.service_account import Credentials
            Credentials.from_service_account_file(dest_path)
            cfg["service_account_path"] = dest_path

            # # ← THÊM DÒNG NÀY: reset cache để lần sau _get_service() tạo lại
            # from Boost.worker import reset_service
            # reset_service()

        except Exception as e:
            errors["service_account"] = f"File JSON không hợp lệ: {str(e)}"
            os.remove(dest_path)
    elif not cfg.get("service_account_path"):
        errors["service_account"] = "Vui lòng upload file service account JSON."

    if errors:
        return jsonify({"ok": False, "errors": errors}), 400

    save_config(cfg)
    return jsonify({"ok": True, "config": cfg})


@fe_bp.route('/start', methods=['POST'])
def start_tool():
    cfg = load_config()

    if not cfg.get("spreadsheet_id"):
        return jsonify({"ok": False, "error": "Chưa có Spreadsheet ID. Lưu cấu hình trước."}), 400
    if not cfg.get("service_account_path") or \
       not os.path.exists(cfg["service_account_path"]):
        return jsonify({"ok": False, "error": "File service account không tồn tại."}), 400

    # Khởi động scheduler nếu chưa chạy
    if not scheduler.running:
        scheduler.start()

    # Mở Sheet trong browser
    webbrowser.open(cfg["sheet_url"])

    cfg["running"] = True
    save_config(cfg)
    return jsonify({"ok": True, "message": "Tool đã khởi động. Sheet đã được mở."})


@fe_bp.route('/stop', methods=['POST'])
def stop_tool():
    """Dừng tất cả process đang chạy + xóa scheduled jobs."""
    with _process_lock:
        targets = list(_active_processes)

    for p in targets:
        if p.is_alive():
            p.terminate()
            p.join(timeout=5)
            if p.is_alive():
                p.kill()

    with _process_lock:
        for p in targets:
            try:
                _active_processes.remove(p)
            except ValueError:
                pass

    scheduler.remove_all_jobs()

    cfg = load_config()
    cfg["running"] = False
    save_config(cfg)

    return jsonify({
        "ok":      True,
        "stopped": len(targets),
        "message": f"Đã dừng {len(targets)} process và xóa tất cả scheduled jobs."
    })


@fe_bp.route('/status')
def status():
    cfg = load_config()
    with _process_lock:
        active_count = len(_active_processes)
    job_count = len(scheduler.get_jobs())

    return jsonify({
        "running":        cfg.get("running", False),
        "sheet_url":      cfg.get("sheet_url", ""),
        "spreadsheet_id": cfg.get("spreadsheet_id", ""),
        "has_json":       bool(
            cfg.get("service_account_path") and
            os.path.exists(cfg.get("service_account_path", ""))
        ),
        "active_processes": active_count,
        "scheduled_jobs":   job_count,
    })


@fe_bp.route('/shutdown', methods=['POST'])
def shutdown():
    def _kill():
        time.sleep(0.5)
        os._exit(0)
    threading.Thread(target=_kill, daemon=True).start()
    return jsonify({"ok": True})
