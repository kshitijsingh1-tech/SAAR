import React, { useState, useRef } from 'react';
import { Eye, Radio, Upload, Sparkles, Link as LinkIcon, Camera, X } from 'lucide-react';

export const ImageInspector = ({
  preset,
  activeStep,
  customImageData,
  customImageUrl,
  onImageUploaded,
  vlmProviderUsed,
  cameraConnected,
  onCloseCamera
}) => {
  const [urlInput, setUrlInput] = useState('');
  const [showUrlInput, setShowUrlInput] = useState(false);
  const fileInputRef = useRef(null);

  const displayImage = customImageData || customImageUrl || preset?.image;

  // Render ONLY if camera connected or visual image data present
  if (!cameraConnected && !customImageData && !customImageUrl) {
    return null;
  }

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (uploadEvent) => {
        onImageUploaded(uploadEvent.target.result, null);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleUrlSubmit = (e) => {
    e.preventDefault();
    if (urlInput.trim()) {
      onImageUploaded(null, urlInput.trim());
      setShowUrlInput(false);
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '1.25rem', marginBottom: '1rem', display: 'flex', flexDirection: 'column' }}>
      {/* Panel Header */}
      <div className="panel-title" style={{ justifyContent: 'space-between', marginBottom: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Camera size={18} color="var(--primary)" />
          <span>Connected Camera Feed &amp; Visual Evidence Monitor</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          {/* Live Token Auto Router Status */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            padding: '0.2rem 0.6rem',
            borderRadius: '12px',
            background: 'rgba(16, 185, 129, 0.15)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            fontSize: '0.72rem',
            color: 'var(--emerald)',
            fontFamily: 'var(--font-mono)',
            fontWeight: '600'
          }}>
            <Sparkles size={12} />
            <span>{vlmProviderUsed || 'Auto Token Router (Active)'}</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.75rem', color: 'var(--emerald)', fontFamily: 'var(--font-mono)' }}>
            <Radio size={14} className="spin" style={{ animationDuration: '3s' }} />
            <span>LIVE STREAM</span>
          </div>

          {onCloseCamera && (
            <button onClick={onCloseCamera} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
              <X size={16} />
            </button>
          )}
        </div>
      </div>

      {/* Toolbar Controls */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '0.75rem',
        padding: '0.5rem 0.75rem',
        borderRadius: '8px',
        background: 'var(--bg-dark)',
        border: '1px solid var(--border-color)',
        fontSize: '0.8rem',
        gap: '0.5rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept="image/*"
            style={{ display: 'none' }}
          />
          <button
            className="btn btn-secondary"
            onClick={() => fileInputRef.current?.click()}
            style={{ padding: '0.25rem 0.6rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}
          >
            <Upload size={13} />
            Upload Image Frame
          </button>
          
          <button
            className="btn btn-secondary"
            onClick={() => setShowUrlInput(!showUrlInput)}
            style={{ padding: '0.25rem 0.6rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}
          >
            <LinkIcon size={13} />
            Stream URL
          </button>
        </div>

        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          <span>Auto Token Routing Enabled</span>
        </div>
      </div>

      {/* URL Input Row */}
      {showUrlInput && (
        <form onSubmit={handleUrlSubmit} style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
          <input
            type="url"
            placeholder="Paste camera stream or image URL..."
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            style={{
              flex: 1,
              padding: '0.4rem 0.6rem',
              borderRadius: '6px',
              border: '1px solid var(--border-color)',
              background: 'var(--bg-dark)',
              color: 'var(--text-main)',
              fontSize: '0.8rem'
            }}
          />
          <button type="submit" className="btn btn-primary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}>
            Load Stream
          </button>
        </form>
      )}

      {/* 16:9 Camera Feed Monitor */}
      <div style={{
        position: 'relative',
        width: '100%',
        aspectRatio: '16 / 9',
        borderRadius: '10px',
        overflow: 'hidden',
        border: '1px solid var(--border-color)',
        background: '#000000',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        {displayImage ? (
          <img
            src={displayImage}
            alt="Camera Evidence Feed"
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover'
            }}
          />
        ) : (
          <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
            <Camera size={36} style={{ opacity: 0.5, marginBottom: '0.5rem' }} />
            <div>Camera Stream Connected (1080p HD)</div>
          </div>
        )}

        <div style={{
          position: 'absolute',
          bottom: 10,
          left: 12,
          right: 12,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'rgba(0, 0, 0, 0.65)',
          backdropFilter: 'blur(8px)',
          padding: '0.4rem 0.75rem',
          borderRadius: '6px',
          color: '#ffffff',
          fontSize: '0.75rem'
        }}>
          <div style={{ fontWeight: '600' }}>
            {preset?.title || "Live Connected Camera Stream"}
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--emerald)' }}>
            FPS: 60 | 1080p HD
          </div>
        </div>
      </div>
    </div>
  );
};
