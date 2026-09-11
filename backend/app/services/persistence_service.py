"""
Saar (सार) — JSON-on-Disk Persistence Service
Lightweight file-based persistence for investigation states and temporal snapshots.
No external DB dependencies — uses pathlib + json with atomic write-rename.
"""
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


# Root data directory (relative to backend/)
DATA_ROOT = Path(__file__).resolve().parent.parent.parent / "data" / "investigations"


class PersistenceService:
    """Thread-safe, file-based persistence for SAAR investigations."""

    def __init__(self, data_root: Optional[Path] = None):
        self.root = data_root or DATA_ROOT
        self.root.mkdir(parents=True, exist_ok=True)

    def _inv_dir(self, inv_id: str) -> Path:
        """Get or create the directory for a specific investigation."""
        d = self.root / inv_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _snapshots_dir(self, inv_id: str) -> Path:
        """Get or create the snapshots subdirectory."""
        d = self._inv_dir(inv_id) / "snapshots"
        d.mkdir(parents=True, exist_ok=True)
        return d

    # ------------------------------------------------------------------
    # Atomic write helper (write to temp → rename to target)
    # ------------------------------------------------------------------

    @staticmethod
    def _atomic_write(filepath: Path, data: dict):
        """Write JSON atomically: write to temp file, then rename."""
        dir_path = filepath.parent
        dir_path.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=str(dir_path), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str, ensure_ascii=False)
            # Atomic rename (on same filesystem)
            os.replace(tmp_path, str(filepath))
        except Exception:
            # Clean up temp file on failure
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    # ------------------------------------------------------------------
    # Investigation State CRUD
    # ------------------------------------------------------------------

    def save_investigation(self, inv_id: str, state_dict: Dict[str, Any]):
        """Persist a full investigation state to disk."""
        filepath = self._inv_dir(inv_id) / "state.json"
        # Add persistence metadata
        state_dict["_persisted_at"] = datetime.now().isoformat()
        self._atomic_write(filepath, state_dict)

    def load_investigation(self, inv_id: str) -> Optional[Dict[str, Any]]:
        """Load an investigation state from disk. Returns None if not found."""
        filepath = self._inv_dir(inv_id) / "state.json"
        if not filepath.exists():
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[PersistenceService] Warning: Could not load {filepath}: {e}")
            return None

    def list_investigations(self) -> List[Dict[str, Any]]:
        """List all persisted investigation IDs with metadata."""
        results = []
        if not self.root.exists():
            return results
        for child in sorted(self.root.iterdir()):
            if child.is_dir() and (child / "state.json").exists():
                try:
                    with open(child / "state.json", "r", encoding="utf-8") as f:
                        state = json.load(f)
                    snapshots_dir = child / "snapshots"
                    snapshot_count = len(list(snapshots_dir.glob("day_*.json"))) if snapshots_dir.exists() else 0
                    results.append({
                        "investigation_id": state.get("investigation_id", child.name),
                        "domain": state.get("dataset_id", "unknown"),
                        "status": state.get("status", "unknown"),
                        "is_longitudinal": state.get("is_longitudinal", False),
                        "day_count": snapshot_count,
                        "overall_confidence": state.get("overall_confidence", 0.0),
                        "created_at": state.get("created_at", ""),
                        "last_updated": state.get("_persisted_at", ""),
                    })
                except Exception as e:
                    print(f"[PersistenceService] Warning: Skipping {child.name}: {e}")
        return results

    def delete_investigation(self, inv_id: str) -> bool:
        """Remove an investigation and all its snapshots from disk."""
        inv_dir = self.root / inv_id
        if not inv_dir.exists():
            return False
        import shutil
        shutil.rmtree(str(inv_dir), ignore_errors=True)
        return True

    # ------------------------------------------------------------------
    # Temporal Snapshots
    # ------------------------------------------------------------------

    def save_snapshot(self, inv_id: str, day_index: int, snapshot_dict: Dict[str, Any]):
        """Persist a single temporal snapshot for a specific day."""
        filepath = self._snapshots_dir(inv_id) / f"day_{day_index:04d}.json"
        snapshot_dict["_saved_at"] = datetime.now().isoformat()
        self._atomic_write(filepath, snapshot_dict)

    def load_snapshot(self, inv_id: str, day_index: int) -> Optional[Dict[str, Any]]:
        """Load a single temporal snapshot."""
        filepath = self._snapshots_dir(inv_id) / f"day_{day_index:04d}.json"
        if not filepath.exists():
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def load_all_snapshots(self, inv_id: str) -> List[Dict[str, Any]]:
        """Load all temporal snapshots for an investigation, ordered by day index."""
        snapshots_dir = self._snapshots_dir(inv_id)
        results = []
        for fp in sorted(snapshots_dir.glob("day_*.json")):
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    results.append(json.load(f))
            except (json.JSONDecodeError, IOError):
                continue
        return results

    def get_snapshot_count(self, inv_id: str) -> int:
        """Count the number of temporal snapshots for an investigation."""
        snapshots_dir = self._snapshots_dir(inv_id)
        if not snapshots_dir.exists():
            return 0
        return len(list(snapshots_dir.glob("day_*.json")))


# Module-level singleton
persistence_service = PersistenceService()
