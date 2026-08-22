import threading, logging
from multiprocessing import Process
from flask import Blueprint, jsonify
from config import load_config, get_spreadsheet_id, save_config
from worker.worker import get_bold_phone_rows, get_bold_phone_rows_2
from controller.posting import running_post_video
from controller.trust import main as running_trust_flow
from controller.boost import running_buff_view
from controller.update import update_avatar, update_bio, update_name

main_run_bp = Blueprint('main_run_bp', __name__)

import threading as _threading
_process_lock    = _threading.Lock()
_active_processes: list = []

def _register_and_run(processes: list):
    with _process_lock:
        _active_processes.extend(processes)
    for p in processes:
        p.start()
    for p in processes:
        p.join()
    with _process_lock:
        for p in processes:
            try:
                _active_processes.remove(p)
            except ValueError:
                pass

def _run_process_later(target_func, args=()):
    """Helper cho scheduler gọi delayed process."""
    p = Process(target=target_func, args=args)
    with _process_lock:
        _active_processes.append(p)
    p.start()

# ── Batch functions ───────────────────────────────────────────────────────────

def _run_immediate_batch(target_func, getter_func, sheet_name: str):
    """
    Chạy ngay tất cả rows không có trigger.
    Phần có trigger sẽ được xử lý bởi run_scheduler blueprint.
    Hàm này chỉ xử lý rows có date == None.
    """
    sid = get_spreadsheet_id()
    if not sid:
        logging.exception("Worker crashed")
        return

    rows = getter_func(spreadsheet_id=sid, sheet_name=sheet_name)
    if not rows:
        return

    processes = [
        Process(target=target_func, args=(row,))
        for row in rows
    ]
    if processes:
        _register_and_run(processes)

# ── API Routes ────────────────────────────────────────────────────────────────
# Tất cả route dưới /api/ prefix (được set khi register_blueprint)



@main_run_bp.route('/start-seeding', methods=['GET', 'POST'])
def trigger_seeding():
    """POST /api/start-seeding"""
    threading.Thread(
        target=_run_immediate_batch,
        args=(running_buff_view, get_bold_phone_rows_2, "seeding_2"),
        daemon=True
    ).start()
    return jsonify({"status": "success", "message": "Seeding started"})


@main_run_bp.route('/start-posting', methods=['GET', 'POST'])
def trigger_posting():
    """POST /api/start-posting"""
    threading.Thread(
        target=_run_immediate_batch,
        args=(running_post_video, get_bold_phone_rows, "seeding"),
        daemon=True
    ).start()
    return jsonify({"status": "success", "message": "Posting started"})


@main_run_bp.route('/start-flow', methods=['GET', 'POST'])
def trigger_flow():
    """POST /api/start-flow"""
    threading.Thread(
        target=_run_immediate_batch,
        args=(running_trust_flow, get_bold_phone_rows, "seeding"),
        daemon=True
    ).start()
    return jsonify({"status": "success", "message": "Trust flow started"})

@main_run_bp.route('/start-update-bio', methods=['GET', 'POST'])
def trigger_update_bio():
    """POST /api/start-update-bio"""
    threading.Thread(
        target=_run_immediate_batch,
        args=(update_bio, get_bold_phone_rows, "seeding"),
        daemon=True
    ).start()
    return jsonify({"status": "success", "message": "Update bio started"})

@main_run_bp.route('/start-update-name', methods=['GET', 'POST'])
def trigger_update_name():
    """POST /api/start-update-name"""
    threading.Thread(
        target=_run_immediate_batch,
        args=(update_name, get_bold_phone_rows, "seeding"),
        daemon=True
    ).start()
    return jsonify({"status": "success", "message": "Update name started"})

@main_run_bp.route('/start-update-avatar', methods=['GET', 'POST'])
def trigger_update_avatar():
    """POST /api/start-update-avatar"""
    threading.Thread(
        target=_run_immediate_batch,
        args=(update_avatar, get_bold_phone_rows, "seeding"),
        daemon=True
    ).start()
    return jsonify({"status": "success", "message": "Update avatar started"})

@main_run_bp.route('/stop', methods=['GET','POST'])
def stop_tool():
    """Dừng tất cả process đang chạy + xóa scheduled jobs."""
    with _process_lock:
        targets = list(_active_processes)

    if not targets:
        return jsonify({"status": "success", "message": "No active processes to stop.", "stopped": 0})

    for p in targets:
        if p.is_alive():
            logging.info("Terminating process %s from stop route", p)
            p.terminate()
            p.join(timeout=5)
            if p.is_alive():
                logging.warning("Process %s did not exit, forcing kill", p)
                p.kill()  # force-kill if still alive after 5 s

    with _process_lock:
        for p in targets:
            try:
                _active_processes.remove(p)
            except ValueError:
                pass

    return jsonify({"status": "success", "message": f"Stopped {len(targets)} process(es).", "stopped": len(targets)})
