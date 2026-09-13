"""
Badminton v1 REST API Router.
Implements the asynchronous endpoints specified in Section 28 of the Master Spec:
- POST /api/v1/videos/upload
- POST /api/v1/analysis/start
- GET  /api/v1/analysis/{job_id}
- GET  /api/v1/analysis/{job_id}/progress
- GET  /api/v1/analysis/{job_id}/report
- GET  /api/v1/analysis/{job_id}/rallies
- GET  /api/v1/analysis/{job_id}/shots
- GET  /api/v1/analysis/{job_id}/movement
- GET  /api/v1/analysis/{job_id}/coverage
- GET  /api/v1/analysis/{job_id}/pose
- GET  /api/v1/analysis/{job_id}/speed
- GET  /api/v1/analysis/{job_id}/energy
- GET  /api/v1/analysis/{job_id}/recommendations
"""
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, UploadFile, File, Query, HTTPException, status
from pydantic import BaseModel

from .jobs import job_manager, JobStage
from .schemas import (
    PlayerMetadata,
    VideoUploadResponse,
    CourtCalibration,
    ManualCourtCalibrationRequest
)
from .court_detector import BadmintonCourtDetector

router = APIRouter(prefix="/api/v1", tags=["Badminton Analysis v1"])


class StartAnalysisRequest(BaseModel):
    job_id: str


@router.post(
    "/videos/upload",
    response_model=VideoUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload video and extract metadata (Phase 1)"
)
async def upload_badminton_video(
    video: UploadFile = File(...),
    player_age: Optional[int] = Query(None, ge=5, le=100),
    player_sex: Optional[str] = Query(None),
    body_weight_kg: Optional[float] = Query(None, ge=20.0, le=250.0),
    skill_level: Optional[str] = Query(None),
    session_duration_min: Optional[float] = Query(None, ge=1.0, le=300.0),
    match_type: Optional[str] = Query(None),
    court_orientation: Optional[str] = Query(None)
):
    """
    Phase 1 Video Ingestion:
    Validates format, reads container headers (FPS, resolution, duration),
    evaluates recording suitability (lighting, blur, jitter), and returns VideoMetadata.
    """
    if not video.filename:
        raise HTTPException(status_code=400, detail="Missing filename in upload.")

    # Validate file extension
    valid_exts = (".mp4", ".mov", ".avi", ".mkv", ".webm")
    if not video.filename.lower().endswith(valid_exts):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported container format. Accepted formats: {', '.join(valid_exts)}"
        )

    try:
        content = await video.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read video stream: {str(e)}")

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Supplied video file is empty (0 bytes).")

    player_meta = None
    if any(p is not None for p in [player_age, player_sex, body_weight_kg, skill_level, session_duration_min, match_type, court_orientation]):
        player_meta = PlayerMetadata(
            age=player_age,
            sex=player_sex,
            body_weight_kg=body_weight_kg,
            skill_level=skill_level,
            session_duration_min=session_duration_min,
            match_type=match_type,
            court_orientation=court_orientation
        )

    try:
        response = job_manager.create_upload_job(
            video_bytes=content,
            filename=video.filename,
            player_metadata=player_meta
        )
        return response
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Video ingestion error: {str(exc)}")


@router.post("/analysis/start", summary="Trigger asynchronous analysis job")
def start_analysis(req: StartAnalysisRequest):
    """
    Initiates asynchronous multi-stage analysis for an uploaded video job.
    """
    try:
        return job_manager.start_analysis_async(req.job_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Job '{req.job_id}' not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/{job_id}", summary="Get overall analysis job status")
def get_job_status(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return job.to_status_dict()


@router.get("/analysis/{job_id}/progress", summary="Poll analysis progress percentage and stage")
def get_job_progress(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return job.to_progress_dict()


@router.get("/analysis/{job_id}/court", summary="Retrieve court detection and calibration geometry")
def get_court_calibration(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")

    calib = job.court_calibration
    if calib is None and job.result:
        calib = job.result.court_calibration

    if calib is None:
        return {
            "job_id": job_id,
            "is_calibrated": False,
            "uncalibrated_reason": "Court calibration not yet performed or unavailable.",
            "court_mode": "doubles"
        }
    return calib.model_dump()


@router.post("/analysis/{job_id}/court/calibrate", summary="Apply manual 4-corner court calibration override")
def apply_manual_court_calibration(job_id: str, req: ManualCourtCalibrationRequest):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")

    court_mode = req.court_mode or "doubles"
    detector = BadmintonCourtDetector()
    calibration = detector.calibrate_from_manual_corners(
        corners_pixel=req.corners_pixel,
        court_mode=court_mode
    )

    if not calibration.is_calibrated:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid court calibration corners: {calibration.uncalibrated_reason}"
        )

    job.set_court_calibration(calibration)
    return calibration.model_dump()


def _get_completed_job_result(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    if job.stage == JobStage.FAILED:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {job.error}")
    if job.stage != JobStage.COMPLETED or not job.result:
        raise HTTPException(
            status_code=202,
            detail=f"Analysis still in progress (stage: {job.stage.value}, progress: {job.progress * 100:.0f}%)."
        )
    return job.result


@router.get("/analysis/{job_id}/report", summary="Retrieve full canonical analysis report")
def get_analysis_report(job_id: str):
    res = _get_completed_job_result(job_id)
    return res.model_dump()


@router.get("/analysis/{job_id}/rallies", summary="Retrieve segmented rally data")
def get_analysis_rallies(job_id: str):
    res = _get_completed_job_result(job_id)
    # Return rally data or shots structured as rally segments
    return {
        "job_id": job_id,
        "total_shots": len(res.shots),
        "rally_count": 1 if res.shots else 0,
        "shots": [s.model_dump() for s in res.shots],
        "findings": res.findings
    }


@router.get("/analysis/{job_id}/shots", summary="Retrieve shot classification events")
def get_analysis_shots(job_id: str):
    res = _get_completed_job_result(job_id)
    return {
        "job_id": job_id,
        "shot_count": len(res.shots),
        "shots": [s.model_dump() for s in res.shots]
    }


@router.get("/analysis/{job_id}/movement", summary="Retrieve player movement and velocity metrics")
def get_analysis_movement(job_id: str):
    res = _get_completed_job_result(job_id)
    return {
        "job_id": job_id,
        "movement_metrics": res.movement_metrics.model_dump(),
        "speed_metrics": res.speed_metrics.model_dump(),
        "court_calibration": res.court_calibration.model_dump() if res.court_calibration else None
    }


@router.get("/analysis/{job_id}/coverage", summary="Retrieve 9-zone court coverage breakdown")
def get_analysis_coverage(job_id: str):
    res = _get_completed_job_result(job_id)
    return {
        "job_id": job_id,
        "court_metrics": res.court_metrics.model_dump()
    }


@router.get("/analysis/{job_id}/pose", summary="Retrieve 17-joint pose and angular kinematics")
def get_analysis_pose(job_id: str):
    res = _get_completed_job_result(job_id)
    return {
        "job_id": job_id,
        "pose_metrics": res.pose_metrics.model_dump(),
        "pose_frames_count": len(res.pose_frames)
    }


@router.get("/analysis/{job_id}/speed", summary="Retrieve verified speed distributions")
def get_analysis_speed(job_id: str):
    res = _get_completed_job_result(job_id)
    return {
        "job_id": job_id,
        "speed_metrics": res.speed_metrics.model_dump(),
        "limitations": [lim for lim in res.limitations if "speed" in lim.lower() or "shuttle" in lim.lower()]
    }


@router.get("/analysis/{job_id}/energy", summary="Retrieve physiological energy and caloric estimation")
def get_analysis_energy(job_id: str):
    res = _get_completed_job_result(job_id)
    return {
        "job_id": job_id,
        "energy_metrics": res.energy_metrics.model_dump(),
        "player_metadata": res.player_metadata.model_dump() if res.player_metadata else None
    }


@router.get("/analysis/{job_id}/recommendations", summary="Retrieve evidence-grounded recommendations")
def get_analysis_recommendations(job_id: str):
    res = _get_completed_job_result(job_id)
    return {
        "job_id": job_id,
        "recommendations": res.recommendations,
        "findings": res.findings,
        "evidence": [e.model_dump() for e in res.evidence]
    }
