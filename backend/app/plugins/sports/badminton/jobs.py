"""
Badminton Asynchronous Analysis Job Manager.
Implements the asynchronous processing pipeline defined in Sections 27 & 28 of
the SAAR Master Specification. Manages video jobs, stage progression, and thread-safe
progress polling.
"""
import uuid
import time
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime

from .schemas import (
    VideoMetadata,
    JobStage,
    VideoUploadResponse,
    PlayerMetadata,
    BadmintonAnalysisResult
)
from .video_processor import BadmintonVideoProcessor
from .quality import assess_badminton_recording_quality, generate_preview_base64


class BadmintonJob:
    def __init__(
        self,
        job_id: str,
        filename: str,
        video_bytes: bytes,
        metadata: VideoMetadata,
        player_metadata: Optional[PlayerMetadata] = None,
        preview_base64: Optional[str] = None,
        issues: Optional[List[str]] = None,
        suitable: bool = True
    ):
        self.job_id = job_id
        self.filename = filename
        self.video_bytes = video_bytes
        self.metadata = metadata
        self.player_metadata = player_metadata
        self.preview_base64 = preview_base64
        self.issues = issues or []
        self.suitable = suitable

        self.stage: JobStage = JobStage.UPLOADED
        self.progress: float = 0.05
        self.stage_message: str = "Video uploaded and technical metadata extracted."
        self.created_at: str = datetime.utcnow().isoformat() + "Z"
        self.updated_at: str = datetime.utcnow().isoformat() + "Z"

        self.court_calibration: Optional[Any] = None
        self.result: Optional[BadmintonAnalysisResult] = None
        self.error: Optional[str] = None
        self.lock = threading.Lock()

    def set_court_calibration(self, calibration: Any):
        with self.lock:
            self.court_calibration = calibration
            if self.result:
                self.result.court_calibration = calibration
            self.updated_at = datetime.utcnow().isoformat() + "Z"

    def update_stage(self, stage: JobStage, progress: float, message: str):
        with self.lock:
            self.stage = stage
            self.progress = round(min(1.0, max(0.0, progress)), 2)
            self.stage_message = message
            self.updated_at = datetime.utcnow().isoformat() + "Z"

    def set_completed(self, result: BadmintonAnalysisResult):
        with self.lock:
            self.result = result
            self.stage = JobStage.COMPLETED
            self.progress = 1.0
            self.stage_message = "Analysis complete. Performance report generated."
            self.updated_at = datetime.utcnow().isoformat() + "Z"

    def set_failed(self, error_message: str):
        with self.lock:
            self.stage = JobStage.FAILED
            self.error = error_message
            self.stage_message = f"Analysis failed: {error_message}"
            self.updated_at = datetime.utcnow().isoformat() + "Z"

    def to_progress_dict(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "job_id": self.job_id,
                "stage": self.stage.value,
                "progress": self.progress,
                "stage_message": self.stage_message,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
                "is_completed": self.stage == JobStage.COMPLETED,
                "is_failed": self.stage == JobStage.FAILED
            }

    def to_status_dict(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "job_id": self.job_id,
                "filename": self.filename,
                "stage": self.stage.value,
                "progress": self.progress,
                "stage_message": self.stage_message,
                "suitable": self.suitable,
                "issues": self.issues,
                "metadata": self.metadata.model_dump(),
                "created_at": self.created_at,
                "updated_at": self.updated_at,
                "error": self.error,
                "has_report": self.result is not None
            }


class BadmintonJobManager:
    """
    Singleton in-memory Job Manager for video ingestion, asynchronous dispatch,
    and progress tracking.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(BadmintonJobManager, cls).__new__(cls)
                cls._instance._jobs: Dict[str, BadmintonJob] = {}
                cls._instance._video_processor = BadmintonVideoProcessor()
            return cls._instance

    def create_upload_job(
        self,
        video_bytes: bytes,
        filename: str = "badminton_video.mp4",
        player_metadata: Optional[PlayerMetadata] = None
    ) -> VideoUploadResponse:
        """
        Validates the incoming video, extracts technical metadata and preview,
        evaluates recording suitability, and registers a new job in UPLOADED state.
        """
        if not video_bytes or len(video_bytes) == 0:
            raise ValueError(f"Supplied video payload '{filename}' is empty (0 bytes).")

        # Process metadata and extract frames for suitability checks
        metadata, frames_meta, raw_frames = self._video_processor.process_video_bytes(
            video_bytes=video_bytes,
            filename=filename
        )

        # Run suitability and quality gate
        quality_eval = assess_badminton_recording_quality(metadata, raw_frames)
        preview_b64 = metadata.preview_image_base64 or generate_preview_base64(raw_frames)

        # Generate unique Job ID
        job_id = f"job_{uuid.uuid4().hex[:8]}"
        is_suitable = quality_eval.confidence != "REJECT"

        job = BadmintonJob(
            job_id=job_id,
            filename=filename,
            video_bytes=video_bytes,
            metadata=metadata,
            player_metadata=player_metadata,
            preview_base64=preview_b64,
            issues=quality_eval.issues,
            suitable=is_suitable
        )

        with self._lock:
            self._jobs[job_id] = job

        return VideoUploadResponse(
            job_id=job_id,
            status=job.stage.value,
            metadata=metadata,
            preview_base64=preview_b64,
            suitable=is_suitable,
            issues=quality_eval.issues
        )

    def get_job(self, job_id: str) -> Optional[BadmintonJob]:
        with self._lock:
            return self._jobs.get(job_id)

    def start_analysis_async(self, job_id: str) -> Dict[str, Any]:
        """
        Launches the asynchronous pipeline worker thread for the specified job.
        """
        job = self.get_job(job_id)
        if not job:
            raise KeyError(f"Job ID '{job_id}' not found.")

        if job.stage not in (JobStage.UPLOADED, JobStage.FAILED):
            return {
                "job_id": job.job_id,
                "status": job.stage.value,
                "message": f"Job is already running or completed (stage: {job.stage.value})."
            }

        worker_thread = threading.Thread(
            target=self._run_pipeline_worker,
            args=(job,),
            daemon=True
        )
        worker_thread.start()

        return {
            "job_id": job.job_id,
            "status": JobStage.PREPROCESSING.value,
            "message": "Badminton analysis pipeline launched in background."
        }

    def _run_pipeline_worker(self, job: BadmintonJob):
        """
        Executes the multi-stage computer vision and analytics pipeline with progress milestones.
        """
        try:
            from .pipeline import BadmintonPipeline

            # Stage 1: Preprocessing
            job.update_stage(
                JobStage.PREPROCESSING,
                0.15,
                "Decoding video container and normalizing athletic frame sampling..."
            )
            time.sleep(0.1)

            # Stage 2: Court Detection
            job.update_stage(
                JobStage.COURT_DETECTION,
                0.30,
                "Detecting court line geometry and validating metric homography..."
            )
            time.sleep(0.1)

            # Stage 3: Player Tracking
            job.update_stage(
                JobStage.PLAYER_TRACKING,
                0.45,
                "Detecting players and tracking ankle contact positions..."
            )
            time.sleep(0.1)

            # Stage 4: Pose Analysis
            job.update_stage(
                JobStage.POSE_ANALYSIS,
                0.60,
                "Estimating 17-joint COCO poses and temporal joint smoothing..."
            )
            time.sleep(0.1)

            # Stage 5: Shuttle Tracking & Hit Detection
            job.update_stage(
                JobStage.SHUTTLE_TRACKING,
                0.75,
                "Tracking shuttle trajectory and detecting stroke contact frames..."
            )
            time.sleep(0.1)

            # Stage 6: Mathematical Analytics & Report Generation
            job.update_stage(
                JobStage.ANALYTICS,
                0.90,
                "Computing 9-zone coverage, recovery metrics, and physiological energetics..."
            )

            pipeline = BadmintonPipeline()
            result = pipeline.analyze_video_bytes(
                video_bytes=job.video_bytes,
                filename=job.filename,
                player_metadata=job.player_metadata,
                analysis_id=job.job_id,
                court_calibration_override=job.court_calibration
            )

            job.court_calibration = result.court_calibration
            job.set_completed(result)

        except Exception as e:
            job.set_failed(str(e))


job_manager = BadmintonJobManager()
