

import sys
import threading
import time
from datetime import datetime

from error_handling.logging_utils import get_logger

logger = get_logger("run_all_workers")

def log(worker_name, msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [{worker_name}] {msg}")
    # Mirror to log file
    try:
        logger.info("[%s] %s", worker_name, msg)
    except Exception:
        # Never crash due to logging
        pass


def run_in_thread(worker_name, run_fn):
    """Wraps a worker's run_worker() in a thread with crash recovery."""
    def _target():
        while True:
            try:
                log(worker_name, "Starting...")
                run_fn()
            except Exception as e:
                try:
                    logger.exception("[%s] CRASHED — restarting in 10s", worker_name)
                except Exception:
                    pass
                log(worker_name, f"❌ CRASHED: {e} — restarting in 10s")
                time.sleep(10)
    t = threading.Thread(target=_target, name=worker_name, daemon=True)
    t.start()
    return t


def main():
    # ── Parse optional --workers flag ────────────────────────────────
    requested = set()
    if "--workers" in sys.argv:
        idx = sys.argv.index("--workers")
        requested = set(sys.argv[idx + 1:])

    all_workers = {
        # "activation": ("activation_reminder_worker", None),
        # "login":      ("login_reminder_worker",      None),
        # "credit":     ("credit_check_worker",        None),
        # "buy_sub":    ("buy_sub_worker",             None),
        "expiry":     ("expiry_worker",              "run_worker"),
        "cron":       ("cron_to_fetch_data",         "main"),
    }

    # Import only the workers we need
    selected = requested if requested else set(all_workers.keys())

    print("=" * 60)
    print(f"  Email Automation — Worker Runner")
    print(f"  Starting: {', '.join(selected)}")
    print("=" * 60 + "\n")
    logger.info("Worker runner starting. selected=%s", ",".join(sorted(selected)))

    threads = []
    for key in selected:
        if key not in all_workers:
            print(f"⚠️  Unknown worker '{key}' — skipping")
            continue

        module_name, fn_name = all_workers[key]
        try:
            # Dynamically import the worker module
            import importlib
            mod = importlib.import_module(f"workers.{module_name}")
            run_fn = getattr(mod, fn_name or "run_worker")
            t = run_in_thread(key, run_fn)
            threads.append(t)
            log(key, f"✅ Thread started ({module_name})")
            # Stagger worker starts to avoid overwhelming the mail API
            time.sleep(1)
        except Exception as e:
            print(f"❌ Failed to load '{module_name}': {e}")
            logger.exception("Failed to load worker module=%s fn=%s", module_name, fn_name)

    if not threads:
        print("No workers started. Exiting.")
        return

    print(f"\n✅ {len(threads)} worker(s) running. Press Ctrl+C to stop.\n")
    logger.info("%s worker(s) running.", len(threads))

    try:
        while True:
            # Print a heartbeat every 60s showing alive threads
            time.sleep(60)
            alive = [t.name for t in threads if t.is_alive()]
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ♥ Alive workers: {', '.join(alive)}\n")
            logger.info("Heartbeat. alive_workers=%s", ",".join(alive))
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down all workers...")
        logger.info("Shutdown requested (KeyboardInterrupt).")


if __name__ == "__main__":
    main()

