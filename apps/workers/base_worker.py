import os
import time
import threading
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from dotenv import load_dotenv

from database.db import get_db_connection


"""
workers/base_worker.py

Shared utilities for all email automation workers.
Provides:
  - get_db_connection()  — now backed by a global connection pool
  - run_cycle_with_timeout() — runs a single worker cycle in a thread with a max
    wall-clock limit, killing it if it exceeds CYCLE_TIMEOUT_SECONDS
  - run_with_pool() — replaces ThreadPoolExecutor.map(), adds per-future timeout
"""

load_dotenv()

# Max seconds a SINGLE full worker cycle (one pass over all users) may take.
# If exceeded, the cycle is abandoned and the next one starts after the sleep gap.
CYCLE_TIMEOUT_SECONDS = int(os.getenv("WORKER_CYCLE_TIMEOUT_SECONDS", 120))

# Max seconds to wait for a SINGLE USER to be processed inside the thread pool.
PER_USER_TIMEOUT_SECONDS = int(os.getenv("WORKER_PER_USER_TIMEOUT_SECONDS", 30))


# Allow default workers to be configured by env, default to 1 to avoid MailboxConcurrency errors
WORKER_CONCURRENCY = int(os.getenv("WORKER_CONCURRENCY", 1))


def run_with_pool(candidates, process_fn, max_workers=WORKER_CONCURRENCY):
    """
    Submit each candidate to a ThreadPoolExecutor and collect results.
    Each individual task is capped at PER_USER_TIMEOUT_SECONDS.
    Tasks that exceed the timeout are cancelled/logged and skipped.
    """
    if not candidates:
        return

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_fn, c): c for c in candidates}
        for future in as_completed(futures, timeout=PER_USER_TIMEOUT_SECONDS * len(candidates)):
            candidate = futures[future]
            try:
                future.result(timeout=PER_USER_TIMEOUT_SECONDS)
            except TimeoutError:
                email = candidate.get("email", str(candidate))
                print(f"  ⚠️  Timeout processing {email} — skipped.")
            except Exception as exc:
                email = candidate.get("email", str(candidate))
                print(f"  ❌ Error processing {email}: {exc}")


def run_cycle_with_timeout(cycle_fn, worker_name, cycle_timeout=None):
    """
    Run cycle_fn() in a thread. If it doesn't finish within cycle_timeout seconds,
    log a warning and return — the main loop will sleep and try again next cycle.

    This prevents a single stuck DB query or network call from hanging the worker
    forever.
    """
    timeout = cycle_timeout or CYCLE_TIMEOUT_SECONDS
    result = {"done": False, "error": None}

    def _run():
        try:
            cycle_fn()
            result["done"] = True
        except Exception as e:
            result["error"] = e

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(timeout=timeout)

    if t.is_alive():
        print(
            f"\n⚠️  [{worker_name}] Cycle exceeded {timeout}s timeout — "
            f"abandoning cycle, will retry next interval.\n"
        )
    elif result["error"]:
        raise result["error"]


def post_with_retry(url, json_payload, timeout=15, max_retries=3, initial_delay=5):
    """
    POST with retry-on-429.  If the mail API returns 429 (throttled),
    wait and retry up to max_retries times with exponential backoff.
    Returns the Response object (or raises on network error).
    """
    delay = initial_delay
    for attempt in range(1, max_retries + 1):
        resp = requests.post(url, json=json_payload, timeout=timeout)
        if resp.status_code != 429:
            return resp
        # 429 — rate limited, wait and retry
        print(f"    ⏳ 429 throttled (attempt {attempt}/{max_retries}), retrying in {delay}s...")
        time.sleep(delay)
        delay *= 2  # exponential backoff: 5s, 10s, 20s
    # Return the last 429 response if all retries exhausted
    return resp
