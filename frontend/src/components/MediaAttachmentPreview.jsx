import React, { useState, useEffect, useRef } from 'react';
import {
  X, Check, Film, Image as ImageIcon, FileText,
  Play, Pause, AlertCircle, Clock, HardDrive, FileCheck
} from 'lucide-react';

/**
 * Format bytes into clean human-readable string (KB/MB)
 */
function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

/**
 * Format seconds into mm:ss
 */
function formatDuration(seconds) {
  if (!seconds || isNaN(seconds)) return '0:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
}

/**
 * MediaAttachmentPreview
 * Compact, modern attachment preview popover inside chat composer.
 */
export function MediaAttachmentPreview({
  file,
  onConfirm,
  onCancel
}) {
  const [previewUrl, setPreviewUrl] = useState(null);
  const [videoDuration, setVideoDuration] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [error, setError] = useState(null);
  const videoRef = useRef(null);

  const fileName = file?.name || 'attachment';
  const fileType = (file?.type || '').toLowerCase();
  const fileSize = file?.size || 0;

  const isVideo = fileType.startsWith('video/') || /\.(mp4|mov|webm|avi|mkv)$/i.test(fileName);
  const isImage = fileType.startsWith('image/') || /\.(png|jpe?g|webp|gif|bmp|svg)$/i.test(fileName);
  const isDataset = /\.(csv|xlsx?|tsv|txt)$/i.test(fileName) || fileType.includes('csv') || fileType.includes('spreadsheet');

  // Generate object URL for preview
  useEffect(() => {
    if (!file) {
      setPreviewUrl(null);
      return;
    }

    if (fileSize === 0) {
      setError('File is empty (0 bytes).');
      return;
    }

    if (fileSize > 150 * 1024 * 1024) {
      setError('File size exceeds maximum 150MB limit.');
      return;
    }

    if (isVideo || isImage) {
      try {
        const url = URL.createObjectURL(file);
        setPreviewUrl(url);
        return () => {
          URL.revokeObjectURL(url);
        };
      } catch (err) {
        setError('Unable to generate local preview.');
      }
    }
  }, [file]);

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setVideoDuration(videoRef.current.duration);
    }
  };

  const toggleVideoPlayback = (e) => {
    e.stopPropagation();
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
      setIsPlaying(false);
    } else {
      videoRef.current.play().then(() => setIsPlaying(true)).catch(() => {});
    }
  };

  if (!file) return null;

  return (
    <div className="media-attachment-popover animate-fade-in" role="dialog" aria-label="Media Attachment Preview">
      <div className="attachment-popover-card">
        {/* Header with Title & Cancel */}
        <div className="attachment-popover-header">
          <div className="attachment-header-title">
            {isVideo ? <Film size={15} className="text-sky" /> : isImage ? <ImageIcon size={15} className="text-emerald" /> : <FileText size={15} className="text-purple" />}
            <span>{isVideo ? 'Video Attachment' : isImage ? 'Image Attachment' : 'Dataset File'}</span>
          </div>
          <button
            type="button"
            className="attachment-close-btn"
            onClick={onCancel}
            title="Cancel & discard attachment"
            aria-label="Cancel attachment"
          >
            <X size={15} />
          </button>
        </div>

        {/* Content Body */}
        <div className="attachment-popover-body">
          {/* Visual Preview Area */}
          <div className="attachment-visual-wrapper">
            {isImage && previewUrl && (
              <div className="attachment-image-frame">
                <img
                  src={previewUrl}
                  alt={fileName}
                  className="attachment-img-preview"
                />
              </div>
            )}

            {isVideo && previewUrl && (
              <div className="attachment-video-frame" onClick={toggleVideoPlayback}>
                <video
                  ref={videoRef}
                  src={previewUrl}
                  playsInline
                  muted
                  onLoadedMetadata={handleLoadedMetadata}
                  onEnded={() => setIsPlaying(false)}
                  className="attachment-video-player"
                />
                <button
                  type="button"
                  className="attachment-play-overlay-btn"
                  onClick={toggleVideoPlayback}
                  aria-label={isPlaying ? 'Pause video preview' : 'Play video preview'}
                >
                  {isPlaying ? <Pause size={18} /> : <Play size={18} style={{ marginLeft: '2px' }} />}
                </button>
                {videoDuration !== null && (
                  <span className="attachment-duration-pill">
                    <Clock size={11} />
                    {formatDuration(videoDuration)}
                  </span>
                )}
              </div>
            )}

            {isDataset && (
              <div className="attachment-doc-frame">
                <FileText size={36} className="text-purple" />
                <span className="doc-extension-badge">{fileName.split('.').pop()?.toUpperCase() || 'DATA'}</span>
              </div>
            )}

            {!isImage && !isVideo && !isDataset && (
              <div className="attachment-doc-frame">
                <FileCheck size={36} className="text-sky" />
                <span className="doc-extension-badge">{fileName.split('.').pop()?.toUpperCase() || 'FILE'}</span>
              </div>
            )}
          </div>

          {/* Metadata Details */}
          <div className="attachment-meta-column">
            <div className="attachment-filename" title={fileName}>
              {fileName}
            </div>

            <div className="attachment-stats-row">
              <span className="attachment-stat-item">
                <HardDrive size={12} />
                {formatFileSize(fileSize)}
              </span>
              {isVideo && videoDuration !== null && (
                <span className="attachment-stat-item">
                  <Clock size={12} />
                  {formatDuration(videoDuration)}
                </span>
              )}
              <span className="attachment-type-tag">
                {isVideo ? 'Video' : isImage ? 'Photo' : isDataset ? 'Dataset' : 'Document'}
              </span>
            </div>

            {error ? (
              <div className="attachment-error-banner">
                <AlertCircle size={13} />
                <span>{error}</span>
              </div>
            ) : (
              <div className="attachment-help-text">
                {isVideo ? 'Ready for motion analysis & kinematic screening.' : isImage ? 'Ready for multi-modal scene reasoning.' : 'Ready for tabular data ingestion.'}
              </div>
            )}
          </div>
        </div>

        {/* Action Footer */}
        <div className="attachment-popover-footer">
          <button
            type="button"
            className="attachment-btn-cancel"
            onClick={onCancel}
          >
            <X size={14} />
            <span>Cancel</span>
          </button>

          <button
            type="button"
            className="attachment-btn-confirm"
            onClick={onConfirm}
            disabled={Boolean(error)}
          >
            <Check size={14} />
            <span>Use This File</span>
          </button>
        </div>
      </div>
    </div>
  );
}
