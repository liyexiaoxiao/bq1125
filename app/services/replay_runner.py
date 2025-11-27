import copy
import json
import os
import shutil
import sqlite3
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ReplayCase:
    run_id: int
    round_id: int
    payload: dict
    original_strategy: Optional[int] = None
    original_status: Optional[int] = None


class ReplayService:
    def __init__(self, logger, config, app=None):
        self.logger = logger
        self.config = config
        self.app = app
        self._workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.source_db_path = self._resolve_path(getattr(config, "REPLAY_SOURCE_DATABASE_URI", config.DATABASE))
        self.target_db_path = self._resolve_path(getattr(config, "REPLAY_DATABASE_URI", os.path.join("app", "replay.db")))
        self.start_run_id = self._coerce_run_id(getattr(config, "REPLAY_START_RUN_ID", None), "REPLAY_START_RUN_ID")
        self.end_run_id = self._coerce_run_id(getattr(config, "REPLAY_END_RUN_ID", None), "REPLAY_END_RUN_ID")
        self._cases: List[ReplayCase] = []
        self._replay_config = None

    def load_cases(self) -> List[ReplayCase]:
        if not self._prepare_target_db():
            return []

        rows = self._fetch_source_rows()
        cases: List[ReplayCase] = []
        for row in rows:
            case = self._build_case(row)
            if case is None or case.payload.get("in_data") is None:
                self.logger.warn(f"Replay skipped run_id={row.get('run_id')}: missing input payload")
                continue
            cases.append(case)

        self._cases = cases
        self.logger.info(
            f"Replay source range start={self.start_run_id} end={self.end_run_id} total_cases={len(cases)}"
        )
        self.logger.info(f"Replay collected {len(cases)} historical inputs for execution")
        return cases

    def get_replay_config(self):
        if self._replay_config is None:
            cfg = copy.deepcopy(self.config)
            cfg.SQLALCHEMY_DATABASE_URI = self.target_db_path
            cfg.DATABASE = self.target_db_path
            self._replay_config = cfg
        return self._replay_config

    def _prepare_target_db(self) -> bool:
        if not self.source_db_path or not os.path.exists(self.source_db_path):
            self.logger.error(f"Replay source database not found: {self.source_db_path}")
            return False

        if os.path.abspath(self.source_db_path) == os.path.abspath(self.target_db_path):
            self.logger.error("Replay target database must differ from source database to avoid data loss")
            return False

        target_dir = os.path.dirname(self.target_db_path)
        if target_dir:
            os.makedirs(target_dir, exist_ok=True)

        if not os.path.exists(self.target_db_path):
            shutil.copyfile(self.source_db_path, self.target_db_path)
        self._clear_target_tables()
        return True

    def _clear_target_tables(self) -> None:
        tables = ["test_runs", "test_error_log", "test_run_log_relation", "pro_input"]
        conn = sqlite3.connect(self.target_db_path)
        try:
            cursor = conn.cursor()
            for table in tables:
                try:
                    cursor.execute(f"DELETE FROM {table}")
                except sqlite3.OperationalError:
                    continue
            conn.commit()
        finally:
            conn.close()

    def _fetch_source_rows(self) -> List[dict]:
        conn = sqlite3.connect(self.source_db_path)
        conn.row_factory = sqlite3.Row
        try:
            conditions = []
            params = []
            if self.start_run_id is not None:
                conditions.append("run_id >= ?")
                params.append(self.start_run_id)
            if self.end_run_id is not None:
                conditions.append("run_id <= ?")
                params.append(self.end_run_id)

            sql = (
                "SELECT run_id, round_id, actual_input, expected_output, "
                "expected_error_output, expected_stuck_output, expected_duration, "
                "type, strategy, status FROM test_runs"
            )
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            sql += " ORDER BY run_id ASC"

            cursor = conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def _build_case(self, row: dict) -> Optional[ReplayCase]:
        actual_input = self._safe_json_loads(row.get("actual_input"))
        expected_output = self._safe_json_loads(row.get("expected_output")) or []
        expected_error = self._safe_json_loads(row.get("expected_error_output"))
        expected_stuck = self._safe_json_loads(row.get("expected_stuck_output"))

        error_entries = []
        if expected_error:
            error_entries.append({"error_type": 1, "out_data": expected_error})
        if expected_stuck:
            error_entries.append({"error_type": 2, "out_data": expected_stuck})

        payload = {
            "type": row.get("type"),
            "in_data": actual_input,
            "expected_results": expected_output,
            "error": error_entries,
            "est_time": self._convert_duration(row.get("expected_duration")),
        }

        return ReplayCase(
            run_id=row.get("run_id"),
            round_id=row.get("round_id"),
            payload=payload,
            original_strategy=row.get("strategy"),
            original_status=row.get("status"),
        )

    @staticmethod
    def _convert_duration(duration_ms: Optional[int]) -> int:
        if not duration_ms:
            return 0
        return max(int(duration_ms / 1000), 0)

    def _resolve_path(self, path: Optional[str]) -> Optional[str]:
        if path is None:
            return None
        if os.path.isabs(path):
            return path
        return os.path.abspath(os.path.join(self._workspace_root, path))

    def _safe_json_loads(self, raw):
        if raw in (None, ""):
            return None
        if isinstance(raw, (dict, list)):
            return raw
        try:
            return json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            self.logger.error("Replay failed to parse stored JSON payload")
            return None

    def _coerce_run_id(self, value, field_name):
        if value in (None, ""):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            self.logger.warn(f"Replay ignored invalid {field_name}={value}")
            return None