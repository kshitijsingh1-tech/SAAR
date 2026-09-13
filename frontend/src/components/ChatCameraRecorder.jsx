import React, { useState, useEffect, useRef } from 'react';
import {
  Camera, X, Play, Pause, RotateCcw, Check,
  AlertCircle, Clock, Video, Loader2, StopCircle, ArrowUp
} from 'lucide-react';

/**
 * Format milliseconds/seconds into mm:ss or ss.s
 */
function formatTimer(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins < 10 ? '0' : ''}${mins}:${secs < 10 ? '0' : ''}${secs}`;
}

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

const MAX_RECORDING_SECONDS = 10;

/**
 * ChatCameraRecorder
 * Native in-browser WebRTC camera recording modal for SAAR chat.
 * Targets ~30 FPS with up to 10-second capture, retake, and real File packaging.
 */
export function ChatCameraRecorder({
  isOpen,
  onClose,
  onCaptureVideo
}) {
  const [stream, setStream] = useState(null);
  const [permissionStatus, setPermissionStatus] = useState('prompt'); // 'prompt' | 'granted' | 'denied' | 'error'
  const [errorMessage, setErrorMessage] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recordedSeconds, setRecordedSeconds] = useState(0);
  const [recordedBlob, setRecordedBlob] = useState(null);
  const [recordedFile, setRecordedFile] = useState(null);
  const [recordedPreviewUrl, setRecordedPreviewUrl] = useState(null);
  const [isPreviewPlaying, setIsPreviewPlaying] = useState(false);
  const [supportedMimeType, setSupportedMimeType] = useState('video/webm');

  const liveVideoRef = useRef(null);
  const previewVideoRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const recordedChunksRef = useRef([]);
  const timerIntervalRef = useRef(null);
  const startTimeRef = useRef(null);

  // Determine best supported MIME type
  useEffect(() => {
    if (typeof MediaRecorder !== 'undefined') {
      const preferredTypes = [
        'video/mp4;codecs=avc1',
        'video/mp4',
        'video/webm;codecs=vp9',
        'video/webm;codecs=vp8',
        'video/webm'
      ];
      for (const t of preferredTypes) {
        if (MediaRecorder.isTypeSupported(t)) {
          setSupportedMimeType(t);
          break;
        }
      }
    }
  }, []);

  // Request & start camera stream
  const startCamera = async () => {
    stopCurrentStream();
    setErrorMessage(null);
    setRecordedBlob(null);
    setRecordedFile(null);
    if (recordedPreviewUrl) {
      URL.revokeObjectURL(recordedPreviewUrl);
      setRecordedPreviewUrl(null);
    }
    setRecordedSeconds(0);
    setIsRecording(false);

    if (!navigator?.mediaDevices?.getUserMedia) {
      setPermissionStatus('error');
      setErrorMessage('Browser does not support camera recording (getUserMedia unavailable).');
      return;
    }

    try {
      const constraints = {
        video: {
          width: { ideal: 1280, min: 640 },
          height: { ideal: 720, min: 480 },
          frameRate: { ideal: 30, max: 30 }
        },
        audio: false // Gait & VLM analysis is visual-only; audio not required
      };

      const userStream = await navigator.mediaDevices.getUserMedia(constraints);
      setStream(userStream);
      setPermissionStatus('granted');

      if (liveVideoRef.current) {
        liveVideoRef.current.srcObject = userStream;
        liveVideoRef.current.play().catch(() => {});
      }
    } catch (err) {
      console.error('Camera access error:', err);
      setPermissionStatus('denied');
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setErrorMessage('Camera access was denied. Please allow camera permissions in your browser address bar.');
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        setErrorMessage('No camera device was detected on this system.');
      } else {
        setErrorMessage(`Camera error: ${err.message || 'Unable to access video camera.'}`);
      }
    }
  };

  const stopCurrentStream = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }
    if (liveVideoRef.current) {
      liveVideoRef.current.srcObject = null;
    }
  };

  // Open/Close Lifecycle
  useEffect(() => {
    if (isOpen) {
      startCamera();
    } else {
      stopRecording();
      stopCurrentStream();
      if (recordedPreviewUrl) {
        URL.revokeObjectURL(recordedPreviewUrl);
        setRecordedPreviewUrl(null);
      }
    }

    return () => {
      stopCurrentStream();
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
      }
    };
  }, [isOpen]);

  // Handle stream assignment when live video ref attaches
  useEffect(() => {
    if (stream && liveVideoRef.current && !recordedBlob) {
      liveVideoRef.current.srcObject = stream;
      liveVideoRef.current.play().catch(() => {});
    }
  }, [stream, recordedBlob]);

  // Start Recording
  const startRecording = () => {
    if (!stream) return;

    recordedChunksRef.current = [];
    setRecordedBlob(null);
    setRecordedFile(null);
    setRecordedSeconds(0);
    setErrorMessage(null);

    try {
      const options = {
        mimeType: supportedMimeType,
        videoBitsPerSecond: 2500000 // 2.5 Mbps crisp recording
      };

      const recorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          recordedChunksRef.current.push(e.data);
        }
      };

      recorder.onstop = () => {
        const ext = supportedMimeType.includes('mp4') ? 'mp4' : 'webm';
        const blob = new Blob(recordedChunksRef.current, { type: supportedMimeType });
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
        const fileName = `camera_walk_clip_${timestamp}.${ext}`;
        const file = new File([blob], fileName, { type: supportedMimeType, lastModified: Date.now() });

        setRecordedBlob(blob);
        setRecordedFile(file);

        const previewUrl = URL.createObjectURL(blob);
        setRecordedPreviewUrl(previewUrl);
        setIsRecording(false);
        stopCurrentStream();
      };

      recorder.start(100); // 100ms chunk interval for smooth capture
      setIsRecording(true);
      startTimeRef.current = Date.now();

      timerIntervalRef.current = setInterval(() => {
        const elapsed = (Date.now() - startTimeRef.current) / 1000;
        setRecordedSeconds(elapsed);

        if (elapsed >= MAX_RECORDING_SECONDS) {
          stopRecording();
        }
      }, 100);
    } catch (err) {
      console.error('Failed to start MediaRecorder:', err);
      setErrorMessage('Failed to initialize video recording stream.');
      setIsRecording(false);
    }
  };

  // Stop Recording
  const stopRecording = () => {
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
      timerIntervalRef.current = null;
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try {
        mediaRecorderRef.current.stop();
      } catch (e) {}
    }
    setIsRecording(false);
  };

  // Retake
  const handleRetake = () => {
    if (recordedPreviewUrl) {
      URL.revokeObjectURL(recordedPreviewUrl);
      setRecordedPreviewUrl(null);
    }
    setRecordedBlob(null);
    setRecordedFile(null);
    setRecordedSeconds(0);
    startCamera();
  };

  // Use Video & optionally Auto-Send directly to backend
  const handleUseVideo = (autoSend = false) => {
    if (!recordedFile) return;
    onCaptureVideo(recordedFile, autoSend);
    onClose();
  };

  const togglePreviewPlayback = () => {
    if (!previewVideoRef.current) return;
    if (isPreviewPlaying) {
      previewVideoRef.current.pause();
      setIsPreviewPlaying(false);
    } else {
      previewVideoRef.current.play().then(() => setIsPreviewPlaying(true)).catch(() => {});
    }
  };

  if (!isOpen) return null;

  return (
    <div className="camera-modal-backdrop animate-fade-in" onClick={onClose} role="dialog" aria-modal="true">
      <div className="camera-modal-card" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="camera-modal-header">
          <div className="camera-header-left">
            <div className="camera-icon-badge">
              <Camera size={16} />
            </div>
            <div>
              <h3 className="camera-modal-title">Record Walking Video</h3>
              <p className="camera-modal-subtitle">Direct 30 FPS camera feed • Up to 10s clip</p>
            </div>
          </div>
          <button
            type="button"
            className="camera-close-btn"
            onClick={onClose}
            title="Close camera"
          >
            <X size={16} />
          </button>
        </div>

        {/* Viewport Body */}
        <div className="camera-viewport-container">
          {/* Permission Prompting / Error */}
          {permissionStatus === 'prompt' && !stream && (
            <div className="camera-state-overlay">
              <Loader2 size={32} className="spin text-primary" />
              <span>Connecting to camera hardware...</span>
            </div>
          )}

          {permissionStatus === 'denied' && (
            <div className="camera-state-overlay error">
              <AlertCircle size={36} color="#ef4444" />
              <div className="camera-error-headline">Camera Permission Needed</div>
              <p className="camera-error-detail">{errorMessage || 'Please enable camera access in your browser settings to record walking clips.'}</p>
              <button
                type="button"
                className="btn-camera-retry"
                onClick={startCamera}
              >
                Try Again
              </button>
            </div>
          )}

          {permissionStatus === 'error' && (
            <div className="camera-state-overlay error">
              <AlertCircle size={36} color="#ef4444" />
              <div className="camera-error-headline">Camera Unavailable</div>
              <p className="camera-error-detail">{errorMessage}</p>
              <button
                type="button"
                className="btn-camera-retry"
                onClick={startCamera}
              >
                Retry Camera
              </button>
            </div>
          )}

          {/* Live Camera Feed */}
          {!recordedBlob && permissionStatus === 'granted' && (
            <div className="camera-video-wrapper">
              <video
                ref={liveVideoRef}
                autoPlay
                playsInline
                muted
                className="camera-live-video"
              />

              {/* Top Bar with Live/Recording Status & Timer */}
              <div className="camera-live-overlay-bar">
                <div className="camera-status-pill">
                  {isRecording ? (
                    <>
                      <span className="rec-pulse-dot" />
                      <span className="rec-label">RECORDING</span>
                    </>
                  ) : (
                    <>
                      <span className="live-green-dot" />
                      <span>LIVE PREVIEW</span>
                    </>
                  )}
                </div>

                <div className={`camera-timer-pill ${isRecording ? 'recording-timer' : ''}`}>
                  <Clock size={12} />
                  <span>
                    {formatTimer(recordedSeconds)} / {formatTimer(MAX_RECORDING_SECONDS)}
                  </span>
                </div>
              </div>

              {/* Guidelines Overlay */}
              {!isRecording && (
                <div className="camera-guidelines-box">
                  <span>Keep toddler's full body and feet visible from side angle at knee height</span>
                </div>
              )}
            </div>
          )}

          {/* Review Recorded Video Clip */}
          {recordedBlob && recordedPreviewUrl && (
            <div className="camera-video-wrapper review-mode">
              <video
                ref={previewVideoRef}
                src={recordedPreviewUrl}
                playsInline
                controls
                onEnded={() => setIsPreviewPlaying(false)}
                className="camera-preview-video"
              />

              <div className="camera-recorded-meta-pill">
                <span>{recordedFile?.name}</span>
                <span>•</span>
                <span>{formatTimer(recordedSeconds)}</span>
                <span>•</span>
                <span>{formatBytes(recordedFile?.size)}</span>
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="camera-modal-footer">
          {/* Live Mode Controls */}
          {!recordedBlob && (
            <div className="camera-controls-row">
              <button
                type="button"
                className="btn-camera-cancel"
                onClick={onClose}
              >
                Cancel
              </button>

              {!isRecording ? (
                <button
                  type="button"
                  className="btn-record-start"
                  onClick={startRecording}
                  disabled={permissionStatus !== 'granted'}
                >
                  <span className="record-red-circle" />
                  <span>Start Recording (10s)</span>
                </button>
              ) : (
                <button
                  type="button"
                  className="btn-record-stop"
                  onClick={stopRecording}
                >
                  <StopCircle size={18} />
                  <span>Stop Recording ({Math.round(recordedSeconds)}s)</span>
                </button>
              )}
            </div>
          )}

          {/* Review Mode Controls */}
          {recordedBlob && (
            <div className="camera-review-controls-row">
              <button
                type="button"
                className="btn-camera-retake"
                onClick={handleRetake}
              >
                <RotateCcw size={15} />
                <span>Retake</span>
              </button>

              <button
                type="button"
                className="btn-camera-use btn-camera-send-now"
                onClick={() => handleUseVideo(true)}
                title="Send directly to backend and analyze gait"
              >
                <ArrowUp size={16} />
                <span>Send &amp; Analyze</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
