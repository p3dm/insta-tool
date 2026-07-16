# # blueprints/run_scheduler.py
# import threading, logging
# from multiprocessing import Process
# from datetime import datetime
# from flask import Blueprint, jsonify

# from apscheduler.triggers.cron import CronTrigger
# from apscheduler.triggers.interval import IntervalTrigger

# # Import CÙNG scheduler singleton
# from scheduler_instance import scheduler

# # Import CÙNG process registry từ main_run
# # → stop_all dùng chung 1 danh sách process, không bị miss process nào
# from blueprints.Run_Main import (
#     _process_lock, _active_processes,
#     _register_and_run, _run_process_later
# )

# from config import get_spreadsheet_id
# from Boost.worker import get_bold_phone_rows
# from Boost.worker_seeding import get_bold_phone_rows_2
# from Boost.worker import running_post_video
# from Boost.worker_seeding import running_buff_view


# schedule_bp = Blueprint('schedule_bp', __name__)

# # ── Trigger resolver ──────────────────────────────────────────────────────────

# def _resolve_trigger(data: dict):
#     """
#     Đọc date / cron_time / interval từ row.
#     Trả về ('date'|'cron'|'interval'|None, value|None)
#     Raise ValueError nếu >1 cột được điền.
#     """
#     raw_date     = data.get("date")
#     raw_cron     = data.get("cron_time")
#     raw_interval = data.get("interval")

#     has = {
#         'date':     raw_date     not in (None, "", 0),
#         'cron':     raw_cron     not in (None, "", 0),
#         'interval': raw_interval not in (None, "", 0),
#     }

#     filled = sum(has.values())

#     if filled == 0:
#         return None, None

#     if filled > 1:
#         conflicts = [f"{k}='{data.get(k)}'" for k, v in has.items() if v]
#         raise ValueError(
#             f"[CONFLICT] Phone ID='{data.get('Phone ID', '?')}': "
#             f"chỉ được điền 1 trigger, hiện có {', '.join(conflicts)}"
#         )

#     if has['date']:
#         return 'date', datetime.strptime(raw_date.strip(), "%d/%m/%Y %H:%M:%S")

#     if has['cron']:
#         h, m = raw_cron.strip().split(":")
#         return 'cron', (int(h), int(m))

#     if has['interval']:
#         return 'interval', int(raw_interval)


# def _schedule_job(target_func, data: dict):
#     try:
#         trigger_type, value = _resolve_trigger(data)
#     except ValueError as e:
#         logging.exception("Worker crashed {e}")
#         return False

#     phone_id = data.get('Phone ID', '?')
#     fname    = target_func.__name__

#     # Không có trigger → trả về Process để caller quyết định
#     if trigger_type is None:
#         return Process(target=target_func, args=(data,))

#     if trigger_type == 'date':
#         scheduler.add_job(
#             _run_process_later,
#             trigger='date',
#             run_date=value,
#             args=[target_func, (data,)],        # ✅ list, đúng thứ tự
#             id=f"date_{fname}_{phone_id}_{value:%Y%m%d%H%M%S}",
#             replace_existing=True
#         )

#     elif trigger_type == 'cron':
#         h, m = value
#         scheduler.add_job(
#             _run_process_later,
#             trigger=CronTrigger(hour=h, minute=m, timezone='Asia/Ho_Chi_Minh'),
#             args=[target_func, (data,)],        # ✅
#             id=f"cron_{fname}_{phone_id}_{h:02d}{m:02d}",
#             replace_existing=True
#         )

#     elif trigger_type == 'interval':
#         scheduler.add_job(
#             _run_process_later,
#             trigger=IntervalTrigger(minutes=value, timezone='Asia/Ho_Chi_Minh'),
#             args=[target_func, (data,)],        # ✅
#             id=f"interval_{fname}_{phone_id}_{value}m",
#             replace_existing=True
#         )
#     return None  # đã lên lịch


# def _run_scheduled_batch(target_func, getter_func, sheet_name: str, label: str):
#     sid = get_spreadsheet_id()
#     if not sid:
#         return

#     rows = getter_func(spreadsheet_id=sid, sheet_name=sheet_name)
#     if not rows:
#         return

#     scheduled = 0
#     skipped   = 0
#     errors    = 0

#     for data in rows:
#         result = _schedule_job(target_func, data)

#         if result is False:
#             # Conflict trigger
#             errors += 1

#         elif result is None:
#             # ✅ Đã lên lịch scheduler
#             scheduled += 1

#         elif isinstance(result, Process):
#             # ✅ Row không có trigger → BỎ QUA, không chạy ngay
#             # Việc chạy ngay đã có /api/... lo
#             skipped += 1

# # ── API Routes ────────────────────────────────────────────────────────────────
# # Prefix: /schedule/ (set khi register_blueprint)

# @schedule_bp.route('/start-up-video', methods=['GET', 'POST'])
# def sched_up_video():
#     """POST /schedule/start-up-video"""
#     threading.Thread(
#         target=_run_scheduled_batch,
#         args=(running_post_video, get_bold_phone_rows, "seeding", "Up Video"),
#         daemon=True
#     ).start()
#     return jsonify({"status": "success", "message": "Scheduled up video started"})


# @schedule_bp.route('/start-seeding', methods=['GET', 'POST'])
# def sched_seeding():
#     """POST /schedule/start-seeding"""
#     threading.Thread(
#         target=_run_scheduled_batch,
#         args=(running_buff_view, get_bold_phone_rows_2, "seeding_2", "Seeding View"),
#         daemon=True
#     ).start()
#     return jsonify({"status": "success", "message": "Scheduled seeding started"})


# @schedule_bp.route('/update-avatar', methods=['GET', 'POST'])
# def sched_avatar():
#     """POST /schedule/update-avatar"""
#     threading.Thread(
#         target=_run_scheduled_batch,
#         args=(update_avatar, get_bold_phone_rows, "seeding", "Update Avatar"),
#         daemon=True
#     ).start()
#     return jsonify({"status": "success", "message": "Scheduled avatar update started"})


# @schedule_bp.route('/update-bio', methods=['GET', 'POST'])
# def sched_bio():
#     """POST /schedule/update-bio"""
#     threading.Thread(
#         target=_run_scheduled_batch,
#         args=(update_bio, get_bold_phone_rows, "seeding", "Update Bio"),
#         daemon=True
#     ).start()
#     return jsonify({"status": "success", "message": "Scheduled bio update started"})


# @schedule_bp.route('/update-name', methods=['GET', 'POST'])
# def sched_name():
#     """POST /schedule/update-name"""
#     threading.Thread(
#         target=_run_scheduled_batch,
#         args=(update_name, get_bold_phone_rows, "seeding", "Update Name"),
#         daemon=True
#     ).start()
#     return jsonify({"status": "success", "message": "Scheduled name update started"})


# @schedule_bp.route('/start-main-flow', methods=['GET', 'POST'])
# def sched_main_flow():
#     """POST /schedule/start-main-flow"""
#     threading.Thread(
#         target=_run_scheduled_batch,
#         args=(main_flow, get_bold_phone_rows, "seeding", "Main Flow"),
#         daemon=True
#     ).start()
#     return jsonify({"status": "success", "message": "Scheduled main flow started"})


# @schedule_bp.route('/clear-jobs', methods=['GET', 'POST'])
# def clear_jobs():
#     """POST /schedule/clear-jobs — xóa tất cả scheduled job"""
#     scheduler.remove_all_jobs()
#     return jsonify({"status": "success", "message": "All scheduled jobs cleared"})


# @schedule_bp.route('/list-jobs', methods=['GET'])
# def list_jobs():
#     """GET /schedule/list-jobs — xem job đang chờ"""
#     jobs = [
#         {
#             "id":       job.id,
#             "func":     str(job.func_ref),
#             "next_run": str(job.next_run_time),
#             "trigger":  str(job.trigger),
#         }
#         for job in scheduler.get_jobs()
#     ]
#     return jsonify({"status": "success", "jobs": jobs, "count": len(jobs)})