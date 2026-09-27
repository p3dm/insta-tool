# blueprints/run_scheduler.py
import threading, logging
from multiprocessing import Process
from datetime import datetime
from flask import Blueprint, jsonify

from apscheduler.triggers.cron import CronTrigger

from scheduler_instance import scheduler

from blueprints.Run_Main import (
    _process_lock, _active_processes,
    _register_and_run, _run_process_later
)

from config import get_spreadsheet_id
from worker.worker import get_bold_phone_rows, get_bold_phone_rows_2
from controller.posting import running_post_video
from controller.boost import running_buff_view
from controller.trust import main as main_flow
from controller.update import update_avatar, update_bio, update_name

# Cột dữ liệu dùng chung cho cả 2 loại trigger, format: dd/mm/yyyy hh:mm:ss
SCHEDULE_COLUMN = "schedule"
DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"

cron_bp = Blueprint('cron_bp', __name__)
date_bp = Blueprint('date_bp', __name__)


# ── Parser dùng chung ─────────────────────────────────────────────────────────

def _parse_schedule_cell(data: dict) -> datetime:
    """
    Đọc cột SCHEDULE_COLUMN, parse theo format dd/mm/yyyy hh:mm:ss.
    Trả về None nếu ô trống. Raise ValueError nếu sai format.
    """
    raw = data.get(SCHEDULE_COLUMN)
    if raw in (None, "", 0):
        return None

    try:
        return datetime.strptime(str(raw).strip(), DATETIME_FORMAT)
    except ValueError:
        raise ValueError(
            f"[FORMAT] Phone ID='{data.get('Phone ID', '?')}': "
            f"giá trị '{raw}' không đúng format '{DATETIME_FORMAT}'"
        )


# ── Trigger resolver riêng cho từng loại ──────────────────────────────────────

def _resolve_date_trigger(data: dict):
    """Lấy nguyên vẹn ngày + giờ để làm run_date."""
    return _parse_schedule_cell(data)


def _resolve_cron_trigger(data: dict):
    """Chỉ lấy phần giờ:phút:giây, bỏ phần ngày → chạy lặp lại hàng ngày."""
    dt = _parse_schedule_cell(data)
    if dt is None:
        return None
    return dt.hour, dt.minute, dt.second


# ── Schedule job: DATE ─────────────────────────────────────────────────────────

def _schedule_date_job(target_func, data: dict):
    try:
        value = _resolve_date_trigger(data)
    except ValueError as e:
        logging.exception(f"Worker crashed {e}")
        return False

    phone_id = data.get('Phone ID', '?')
    fname    = target_func.__name__

    if value is None:
        # Không có ngày → trả Process để caller tự quyết định (không tự chạy ngay)
        return Process(target=target_func, args=(data,))

    scheduler.add_job(
        _run_process_later,
        trigger='date',
        # ``value`` không có offset → hiểu là giờ local của máy chạy app
        run_date=value.replace(tzinfo=scheduler.timezone),
        args=[target_func, (data,)],
        id=f"date_{fname}_{phone_id}_{value:%Y%m%d%H%M%S}",
        replace_existing=True
    )
    return None  # đã lên lịch


# ── Schedule job: CRON ─────────────────────────────────────────────────────────

def _schedule_cron_job(target_func, data: dict):
    try:
        value = _resolve_cron_trigger(data)
    except ValueError as e:
        logging.exception(f"Worker crashed {e}")
        return False

    phone_id = data.get('Phone ID', '?')
    fname    = target_func.__name__

    if value is None:
        return Process(target=target_func, args=(data,))

    h, m, s = value
    scheduler.add_job(
        _run_process_later,
        trigger=CronTrigger(hour=h, minute=m, second=s, timezone=scheduler.timezone),
        args=[target_func, (data,)],
        id=f"cron_{fname}_{phone_id}_{h:02d}{m:02d}{s:02d}",
        replace_existing=True
    )
    return None  # đã lên lịch


# ── Batch runner dùng chung, nhận schedule_fn để tái sử dụng cho cron/date ────

def _run_scheduled_batch(schedule_fn, target_func, getter_func, sheet_name: str, label: str):
    sid = get_spreadsheet_id()
    if not sid:
        return

    rows = getter_func(spreadsheet_id=sid, sheet_name=sheet_name)
    if not rows:
        return

    scheduled = 0
    skipped   = 0
    errors    = 0

    for data in rows:
        result = schedule_fn(target_func, data)

        if result is False:
            # Sai format / lỗi parse
            errors += 1

        elif result is None:
            # ✅ Đã lên lịch scheduler
            scheduled += 1

        elif isinstance(result, Process):
            # ✅ Row không có giá trị → BỎ QUA, không chạy ngay
            skipped += 1

    logging.info(
        f"[{label}] scheduled={scheduled} skipped={skipped} errors={errors}"
    )


# ── Factory tạo route để tránh lặp code cho 5 nghiệp vụ x 2 loại trigger ──────

_JOBS = [
    ("up-video",     "Up Video",       running_post_video, get_bold_phone_rows,   "seeding"),
    ("seeding",      "Seeding View",   running_buff_view,  get_bold_phone_rows_2, "seeding_2"),
    ("update-avatar","Update Avatar",  update_avatar,      get_bold_phone_rows,   "seeding"),
    ("update-bio",   "Update Bio",     update_bio,         get_bold_phone_rows,   "seeding"),
    ("update-name",  "Update Name",    update_name,        get_bold_phone_rows,   "seeding"),
    ("main-flow",    "Main Flow",      main_flow,           get_bold_phone_rows,   "seeding"),
]


def _make_route(blueprint: Blueprint, schedule_fn, route_suffix, label, target_func, getter_func, sheet_name):
    def _view():
        threading.Thread(
            target=_run_scheduled_batch,
            args=(schedule_fn, target_func, getter_func, sheet_name, label),
            daemon=True
        ).start()
        return jsonify({"status": "success", "message": f"Scheduled {label} started"})

    _view.__name__ = f"{blueprint.name}_{route_suffix.replace('-', '_')}"
    blueprint.add_url_rule(f"/{route_suffix}", view_func=_view, methods=["GET", "POST"])


for suffix, label, func, getter, sheet in _JOBS:
    _make_route(cron_bp, _schedule_cron_job, suffix, label, func, getter, sheet)
    _make_route(date_bp, _schedule_date_job, suffix, label, func, getter, sheet)


# ── Quản lý job dùng chung cho cả 2 blueprint ─────────────────────────────────

def _register_job_management(blueprint: Blueprint):
    @blueprint.route('/clear-jobs', methods=['GET', 'POST'])
    def clear_jobs():
        """POST /<prefix>/clear-jobs — xóa tất cả scheduled job"""
        scheduler.remove_all_jobs()
        return jsonify({"status": "success", "message": "All scheduled jobs cleared"})

    @blueprint.route('/jobs/<job_id>', methods=['DELETE'])
    def remove_job(job_id):
        """DELETE /<prefix>/jobs/<job_id> — xóa một scheduled job theo ID."""
        if scheduler.get_job(job_id) is None:
            return jsonify({"status": "error", "message": "Job not found"}), 404
        scheduler.remove_job(job_id)
        return jsonify({"status": "success", "message": "Job removed", "id": job_id})

    @blueprint.route('/list-jobs', methods=['GET'])
    def list_jobs():
        """GET /<prefix>/list-jobs — xem job đang chờ"""
        jobs = []
        for job in scheduler.get_jobs():
            # APScheduler does not set next_run_time while a job is pending
            # (for example, before scheduler.start()).
            next_run = getattr(job, "next_run_time", None)
            jobs.append({
                "id":       job.id,
                "func":     str(job.func_ref),
                "next_run_time": next_run.isoformat() if next_run else "Pending — scheduler chưa chạy",
                "trigger":  str(job.trigger),
            })
        return jsonify({
            "status": "success",
            "jobs": jobs,
            "count": len(jobs),
            "timezone": str(scheduler.timezone),
            "current_time": datetime.now(scheduler.timezone).isoformat(),
        })


_register_job_management(cron_bp)
_register_job_management(date_bp)

# Đăng ký ở app.py:
#   app.register_blueprint(cron_bp, url_prefix='/cron')
#   app.register_blueprint(date_bp, url_prefix='/date')
