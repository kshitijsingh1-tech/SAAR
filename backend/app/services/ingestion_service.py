"""
Saar (सार) — Data Ingestion Service
Handles CSV/XLSX upload, schema detection, column profiling, and entity/feature extraction.
Pure deterministic — NO LLM calls. Statistics only.
"""
import csv
import io
import re
import statistics
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
from datetime import datetime, timedelta

from ..models.saar_models import (
    DatasetProfile, ColumnProfile, FeatureType, SemanticRole,
    Entity, Feature, Observation
)


class IngestionService:
    """Ingests CSV data and produces structured dataset profiles."""

    # Heuristic patterns for semantic role detection
    _TEMPORAL_PATTERNS = re.compile(
        r"(date|time|timestamp|day|month|year|week|period|created|updated)",
        re.IGNORECASE
    )
    _INTERVENTION_PATTERNS = re.compile(
        r"(water|fertiliz|pesticid|irrigat|spray|prun|treat|dosage|applied|intervention|action|campaign|spend|budget)",
        re.IGNORECASE
    )
    _ENVIRONMENTAL_PATTERNS = re.compile(
        r"(temp|humid|rain|wind|solar|uv|pressure|moisture|weather|climate|altitude)",
        re.IGNORECASE
    )
    _STATE_PATTERNS = re.compile(
        r"(health|stress|yellow|growth|disease|damage|score|rating|status|condition|quality|performance)",
        re.IGNORECASE
    )
    _ID_PATTERNS = re.compile(
        r"(^id$|_id$|^name$|^code$|^key$|^index$|^label$)",
        re.IGNORECASE
    )

    def ingest_csv(self, file_content: bytes, filename: str = "upload.csv") -> Tuple[DatasetProfile, List[List[Any]]]:
        """
        Parse CSV or XLSX bytes into a DatasetProfile + raw data rows.
        Returns (profile, rows) where rows is list of dicts.
        """
        rows = []
        fieldnames = []

        # Check if file is XLSX (ZIP binary signature PK\x03\x04)
        if file_content.startswith(b"PK\x03\x04") or filename.lower().endswith((".xlsx", ".xlsm")):
            import zipfile
            import xml.etree.ElementTree as ET
            try:
                with zipfile.ZipFile(io.BytesIO(file_content)) as z:
                    shared_strings = []
                    if "xl/sharedStrings.xml" in z.namelist():
                        tree = ET.fromstring(z.read("xl/sharedStrings.xml"))
                        for si in tree.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si"):
                            t = si.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")
                            shared_strings.append(t.text if t is not None else "")

                    sheet_name = "xl/worksheets/sheet1.xml"
                    if sheet_name in z.namelist():
                        tree = ET.fromstring(z.read(sheet_name))
                        sheet_data = tree.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheetData")
                        parsed_matrix = []
                        for row_elem in sheet_data.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row"):
                            cell_vals = []
                            for c in row_elem.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c"):
                                v = c.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v")
                                val = v.text if v is not None else ""
                                t = c.get("t")
                                if t == "s" and val.isdigit() and int(val) < len(shared_strings):
                                    val = shared_strings[int(val)]
                                cell_vals.append(val.strip())
                            if any(cell_vals):
                                parsed_matrix.append(cell_vals)

                        if parsed_matrix:
                            # Header is first non-empty row
                            raw_header = parsed_matrix[0]
                            fieldnames = [str(h).strip() if str(h).strip() else f"col_{idx+1}" for idx, h in enumerate(raw_header)]
                            for r in parsed_matrix[1:]:
                                row_dict = {}
                                for idx, h in enumerate(fieldnames):
                                    row_dict[h] = r[idx] if idx < len(r) else ""
                                rows.append(row_dict)
            except Exception as e:
                print(f"[IngestionService] XLSX parsing fallback: {e}")

        # Standard CSV Parsing if not XLSX or fallback
        if not rows:
            text = file_content.decode("utf-8-sig", errors="ignore")
            # Universal newline normalization
            lines = [l for l in text.splitlines() if l.strip()]
            if lines:
                reader = csv.DictReader(lines)
                fieldnames = [str(f).strip() for f in (reader.fieldnames or []) if f is not None]
                rows = list(reader)

        if not rows or not fieldnames:
            raise ValueError(f"Uploaded file '{filename}' is empty or has no valid columnar data.")

        columns: List[ColumnProfile] = []
        temporal_cols, numeric_cols, categorical_cols = [], [], []

        for col_name in fieldnames:
            values = [row.get(col_name) for row in rows]
            profile = self._profile_column(col_name, values)
            columns.append(profile)

            if profile.feature_type == FeatureType.TEMPORAL:
                temporal_cols.append(col_name)
            elif profile.feature_type == FeatureType.CONTINUOUS:
                numeric_cols.append(col_name)
            elif profile.feature_type == FeatureType.CATEGORICAL:
                categorical_cols.append(col_name)

        # Generate initial observations
        observations = self._generate_initial_observations(columns, len(rows))

        # Missing data summary
        missing = {c.name: round(c.null_pct, 2) for c in columns if c.null_pct > 0}

        profile = DatasetProfile(
            filename=filename,
            row_count=len(rows),
            column_count=len(fieldnames),
            columns=columns,
            temporal_columns=temporal_cols,
            numeric_columns=numeric_cols,
            categorical_columns=categorical_cols,
            missing_summary=missing,
            initial_observations=observations,
        )

        return profile, rows

    def extract_features(self, profile: DatasetProfile) -> List[Feature]:
        """Extract Feature objects from a DatasetProfile."""
        features = []
        for col in profile.columns:
            if col.semantic_role == SemanticRole.IDENTIFIER:
                continue
            features.append(Feature(
                name=col.name,
                feature_type=col.feature_type,
                semantic_role=col.semantic_role,
                unit=self._guess_unit(col.name),
                description=f"{col.semantic_role.value} variable ({col.feature_type.value})"
            ))
        return features

    def extract_observations(self, rows: List[Dict[str, Any]], profile: DatasetProfile) -> List[Observation]:
        """Convert raw data rows into Observation objects."""
        observations = []
        day_col = None
        date_col = None

        for c in profile.columns:
            c_lower = c.name.lower()
            if c_lower in ("day", "days") or "day_" in c_lower:
                if not day_col: day_col = c.name
            elif any(k in c_lower for k in ("date", "time", "timestamp", "period")):
                if not date_col: date_col = c.name

        if not day_col and not date_col:
            temporal_col = profile.temporal_columns[0] if profile.temporal_columns else None
            if temporal_col:
                if "day" in temporal_col.lower(): day_col = temporal_col
                else: date_col = temporal_col

        for idx, row in enumerate(rows, start=1):
            day_val = row.get(day_col) if day_col else None
            date_val = row.get(date_col) if date_col else None
            ts_str = self._format_combined_timestamp(day_val, date_val, idx)

            for col in profile.columns:
                if col.semantic_role == SemanticRole.IDENTIFIER or col.semantic_role == SemanticRole.TEMPORAL:
                    continue
                raw_val = row.get(col.name)
                if raw_val is None or str(raw_val).strip() == "":
                    continue
                val = self._parse_value(raw_val, col.feature_type)
                observations.append(Observation(
                    feature_name=col.name,
                    value=val,
                    timestamp=ts_str,
                    source=profile.filename,
                ))
        return observations

    def _format_combined_timestamp(self, day_val: Any, date_val: Any, idx: int) -> str:
        day_str = None
        if day_val is not None and str(day_val).strip() != "":
            s_day = str(day_val).strip()
            try:
                f_day = float(s_day)
                if f_day < 1000:
                    day_str = f"Day {int(f_day)}"
                else:
                    day_str = f"Day {s_day}"
            except ValueError:
                day_str = f"Day {s_day}" if not s_day.lower().startswith("day") else s_day

        date_str = None
        if date_val is not None and str(date_val).strip() != "":
            s_date = str(date_val).strip()
            try:
                fval = float(s_date)
                if 30000 <= fval <= 60000:
                    dt = datetime(1899, 12, 30) + timedelta(days=int(fval))
                    date_str = dt.strftime("%Y-%m-%d")
                elif fval >= 1000:
                    date_str = str(int(fval))
                else:
                    date_str = s_date
            except ValueError:
                date_str = s_date

        if day_str and date_str and day_str != date_str:
            return f"{day_str} ({date_str})"
        return day_str or date_str or f"Day {idx}"

    # ------------------------------------------------------------------
    # Column Profiling
    # ------------------------------------------------------------------

    def _profile_column(self, name: str, values: List[Any]) -> ColumnProfile:
        """Profile a single column: dtype, stats, semantic role."""
        clean_vals = [v for v in values if v is not None and str(v).strip() != ""]
        total = len(values)
        non_null = len(clean_vals)
        null_count = total - non_null
        null_pct = (null_count / total * 100) if total > 0 else 0.0

        # Detect data type
        feature_type = self._detect_feature_type(name, clean_vals)
        semantic_role = self._detect_semantic_role(name, feature_type)

        profile = ColumnProfile(
            name=name,
            dtype=feature_type.value,
            feature_type=feature_type,
            semantic_role=semantic_role,
            non_null_count=non_null,
            null_count=null_count,
            null_pct=round(null_pct, 1),
            unique_count=len(set(str(v) for v in clean_vals)),
        )

        # Numeric statistics
        if feature_type == FeatureType.CONTINUOUS:
            nums = []
            for v in clean_vals:
                try:
                    nums.append(float(v))
                except (ValueError, TypeError):
                    pass
            if nums:
                profile.mean = round(statistics.mean(nums), 3)
                profile.median = round(statistics.median(nums), 3)
                profile.std = round(statistics.stdev(nums), 3) if len(nums) > 1 else 0.0
                profile.min_val = round(min(nums), 3)
                profile.max_val = round(max(nums), 3)

        # Categorical top values
        elif feature_type == FeatureType.CATEGORICAL:
            counter = Counter(str(v) for v in clean_vals)
            profile.top_values = [{"value": k, "count": c} for k, c in counter.most_common(5)]

        # Temporal range
        elif feature_type == FeatureType.TEMPORAL:
            str_vals = sorted(str(v) for v in clean_vals)
            if str_vals:
                profile.date_range = {"min": str_vals[0], "max": str_vals[-1]}

        return profile

    def _detect_feature_type(self, name: str, values: List[Any]) -> FeatureType:
        """Heuristically detect the feature type of a column."""
        if not values:
            return FeatureType.UNKNOWN

        # Check temporal first (by name pattern)
        if self._TEMPORAL_PATTERNS.search(name):
            return FeatureType.TEMPORAL

        # Try parsing as numeric
        numeric_count = 0
        for v in values[:50]:  # Sample first 50
            try:
                float(v)
                numeric_count += 1
            except (ValueError, TypeError):
                pass

        if numeric_count / max(1, min(len(values), 50)) > 0.8:
            # Check if binary (0/1)
            unique = set(str(v).strip() for v in values)
            if unique <= {"0", "1", "0.0", "1.0", "True", "False", "true", "false", "yes", "no"}:
                return FeatureType.BINARY
            return FeatureType.CONTINUOUS

        # Check if date-like values
        for v in values[:10]:
            try:
                datetime.fromisoformat(str(v).replace("/", "-"))
                return FeatureType.TEMPORAL
            except (ValueError, TypeError):
                pass

        # Default to categorical
        unique_ratio = len(set(str(v) for v in values)) / max(1, len(values))
        if unique_ratio > 0.8 and len(values) > 20:
            return FeatureType.TEXT
        return FeatureType.CATEGORICAL

    def _detect_semantic_role(self, name: str, ftype: FeatureType) -> SemanticRole:
        """Heuristically detect what role a column plays."""
        if self._ID_PATTERNS.search(name):
            return SemanticRole.IDENTIFIER
        if ftype == FeatureType.TEMPORAL:
            return SemanticRole.TEMPORAL
        if self._INTERVENTION_PATTERNS.search(name):
            return SemanticRole.INTERVENTION
        if self._ENVIRONMENTAL_PATTERNS.search(name):
            return SemanticRole.ENVIRONMENTAL
        if self._STATE_PATTERNS.search(name):
            return SemanticRole.STATE
        return SemanticRole.MEASUREMENT

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _parse_value(self, raw: Any, ftype: FeatureType) -> Any:
        if ftype == FeatureType.CONTINUOUS:
            try:
                return float(raw)
            except (ValueError, TypeError):
                return raw
        if ftype == FeatureType.BINARY:
            s = str(raw).strip().lower()
            return s in ("1", "1.0", "true", "yes")
        return raw

    def _guess_unit(self, name: str) -> Optional[str]:
        n = name.lower()
        if "temp" in n:
            return "°C"
        if "humid" in n or "moisture" in n:
            return "%"
        if "rain" in n:
            return "mm"
        if "growth" in n or "height" in n:
            return "cm"
        if "pressure" in n:
            return "hPa"
        return None

    def _generate_initial_observations(self, columns: List[ColumnProfile], row_count: int) -> List[str]:
        """Generate human-readable initial observations about the dataset."""
        obs = []
        obs.append(f"Dataset contains {row_count} rows across {len(columns)} columns.")

        temporal = [c for c in columns if c.feature_type == FeatureType.TEMPORAL]
        if temporal:
            obs.append(f"Temporal axis detected: {', '.join(c.name for c in temporal)}. Longitudinal analysis enabled.")

        numeric = [c for c in columns if c.feature_type == FeatureType.CONTINUOUS]
        if numeric:
            obs.append(f"{len(numeric)} continuous variables available for correlation analysis: {', '.join(c.name for c in numeric[:6])}.")

        interventions = [c for c in columns if c.semantic_role == SemanticRole.INTERVENTION]
        if interventions:
            obs.append(f"Intervention/event columns detected: {', '.join(c.name for c in interventions)}. Before/after analysis possible.")

        state_vars = [c for c in columns if c.semantic_role == SemanticRole.STATE]
        if state_vars:
            obs.append(f"State/health variables detected: {', '.join(c.name for c in state_vars)}. These may serve as target variables.")

        missing = [c for c in columns if c.null_pct > 10]
        if missing:
            obs.append(f"⚠ {len(missing)} columns have >10% missing data: {', '.join(f'{c.name} ({c.null_pct}%)' for c in missing[:4])}.")

        return obs
