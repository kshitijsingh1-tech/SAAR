import React, { useState, useRef, useMemo, useEffect } from 'react';
import {
  Eye, EyeOff, Radio, Upload, Sparkles, Link as LinkIcon,
  Camera, X, Crosshair, Target, Layers, Activity, Droplets,
  HelpCircle, ExternalLink, Zap, Check, Film, Play, Pause,
  Sprout, RotateCcw, AlertCircle
} from 'lucide-react';
import { VideoTimelineScrubber } from './VideoTimelineScrubber';
import { PlantCareCard } from './PlantCareCard';
import { ToddlerPostureCard } from './ToddlerPostureCard';

// Clean black, white & signature blue palette for visual anchors & bounding boxes
const ANCHOR_COLORS = [
  { stroke: '#38bdf8', fill: 'rgba(56, 189, 248, 0.18)', glow: 'rgba(56, 189, 248, 0.35)', text: '#38bdf8', bg: 'rgba(56, 189, 248, 0.1)', border: 'rgba(56, 189, 248, 0.4)' },
  { stroke: '#38bdf8', fill: 'rgba(56, 189, 248, 0.18)', glow: 'rgba(56, 189, 248, 0.35)', text: '#38bdf8', bg: 'rgba(56, 189, 248, 0.1)', border: 'rgba(56, 189, 248, 0.4)' },
  { stroke: '#38bdf8', fill: 'rgba(56, 189, 248, 0.18)', glow: 'rgba(56, 189, 248, 0.35)', text: '#38bdf8', bg: 'rgba(56, 189, 248, 0.1)', border: 'rgba(56, 189, 248, 0.4)' },
  { stroke: '#38bdf8', fill: 'rgba(56, 189, 248, 0.18)', glow: 'rgba(56, 189, 248, 0.35)', text: '#38bdf8', bg: 'rgba(56, 189, 248, 0.1)', border: 'rgba(56, 189, 248, 0.4)' },
  { stroke: '#38bdf8', fill: 'rgba(56, 189, 248, 0.18)', glow: 'rgba(56, 189, 248, 0.35)', text: '#38bdf8', bg: 'rgba(56, 189, 248, 0.1)', border: 'rgba(56, 189, 248, 0.4)' },
  { stroke: '#38bdf8', fill: 'rgba(56, 189, 248, 0.18)', glow: 'rgba(56, 189, 248, 0.35)', text: '#38bdf8', bg: 'rgba(56, 189, 248, 0.1)', border: 'rgba(56, 189, 248, 0.4)' }
];

// Generic semantic mapping of visual entities to analytical tools & queries
const getDynamicToolMapping = (node) => {
  if (!node) return null;
  const category = String(node.category || '').toLowerCase();
  const label = String(node.label || node.id || '').toLowerCase();

  if (category.includes('patholog') || label.includes('chloros') || label.includes('lesion') || label.includes('burn') || label.includes('stain')) {
    return {
      toolId: 'telemetry',
      toolName: 'Diagnostic Spectral & Pathology Analyzer',
      actionLabel: 'Analyze Foliar/Tissue Pathology',
      suggestedQuery: `Analyze the pathology, discoloration patterns, and diagnostic indicators associated with ${node.label || node.id}.`
    };
  }

  if (category.includes('morpholog') || label.includes('fenestrat') || label.includes('apex') || label.includes('shoot') || label.includes('leaf') || label.includes('margin')) {
    return {
      toolId: 'telemetry',
      toolName: 'Morphological & Phenotyping Profiler',
      actionLabel: 'Analyze Structural Morphology',
      suggestedQuery: `Examine the anatomical structure and developmental vigor of ${node.label || node.id}.`
    };
  }

  if (category.includes('infrastruct') || category.includes('structur') || category.includes('obstacle') || label.includes('road') || label.includes('crack') || label.includes('pipe') || label.includes('drain') || label.includes('emitter')) {
    return {
      toolId: 'telemetry',
      toolName: 'Structural Integrity & Fluid Dynamics Analyzer',
      actionLabel: 'Inspect Structural Entity',
      suggestedQuery: `Assess the failure risk, load fatigue, and environmental exposure affecting ${node.label || node.id}.`
    };
  }

  if (category.includes('biomechan') || category.includes('orthoped') || category.includes('postur') || category.includes('motor') || label.includes('lordosis') || label.includes('gait') || label.includes('stance') || label.includes('bowing')) {
    return {
      toolId: 'telemetry',
      toolName: 'Biomechanical & Kinematic Alignment Evaluator',
      actionLabel: 'Evaluate Postural Alignment',
      suggestedQuery: `Evaluate the biomechanical angles, weight distribution, and developmental alignment of ${node.label || node.id}.`
    };
  }

  if (category.includes('measure') || category.includes('telemetry') || label.includes('sensor') || label.includes('probe') || label.includes('meter')) {
    return {
      toolId: 'telemetry',
      toolName: 'Telemetry & Environmental Sensor Profiler',
      actionLabel: 'Analyze Sensor Telemetry',
      suggestedQuery: `Evaluate the sensor telemetry, threshold exceedances, and environmental trends for ${node.label || node.id}.`
    };
  }

  return {
    toolId: 'telemetry',
    toolName: 'Diagnostic Simulation Tool',
    actionLabel: 'Inspect Regional Evidence',
    suggestedQuery: `Analyze the scientific implications and causal factors associated with ${node.label || node.id}.`
  };
};

export const ImageInspector = ({
  preset,
  presetId,
  activeStep,
  customImageData,
  customImageUrl,
  onImageUploaded,
  onUploadCustom,
  onPasteUrl,
  vlmProviderUsed,
  vlmProvider,
  cameraConnected,
  onCloseCamera,
  nodes = [],
  selectedNodeId,
  onSelectNode,
  onOpenTool,
  onAskQuery,
  onOpenGlossary
}) => {
  const [urlInput, setUrlInput] = useState('');
  const [showUrlInput, setShowUrlInput] = useState(false);
  const [visibleBoxIds, setVisibleBoxIds] = useState(() => new Set());
  const [hoveredBoxId, setHoveredBoxId] = useState(null);
  const [activeHudNode, setActiveHudNode] = useState(null);
  const [activeSpecialistTab, setActiveSpecialistTab] = useState('anchors'); // 'anchors' | 'plantCare' | 'toddlerPosture'
  const fileInputRef = useRef(null);

  // ------------------------------------------------------------------
  // Multimodal Video Playback & Timeline State (Workstream 4)
  // ------------------------------------------------------------------
  const [mediaMode, setMediaMode] = useState('image'); // 'image' | 'video'
  const [videoCurrentTime, setVideoCurrentTime] = useState(0);
  const [videoDuration, setVideoDuration] = useState(12.0);
  const [isVideoPlaying, setIsVideoPlaying] = useState(false);
  const [activeKeyframeIndex, setActiveKeyframeIndex] = useState(0);
  const [customVideoUrl, setCustomVideoUrl] = useState(null);
  const videoRef = useRef(null);

  const isPediatrics = presetId?.startsWith('toddler') || preset?.domain === 'pediatrics';
  const isAgriculture = presetId?.startsWith('agri') || preset?.domain === 'agriculture' || presetId === 'session-3';

  // Pre-configured temporal keyframe streams for video analysis demonstrations
  const temporalKeyframes = useMemo(() => {
    if (isPediatrics) {
      return [
        {
          timestamp: 0.0,
          label: 'Initial Stance & Plumb Axis',
          category: 'biomechanics',
          confidence: 0.96,
          nodes: [
            { id: 'toddler_spine', label: 'Spinal Lumbar Curve (~38.5°)', bbox: [320, 290, 610, 520], confidence: 0.94, category: 'biomechanics', properties: { lordosis_deg: 38.5, status: 'physiologic' } },
            { id: 'toddler_stance', label: 'Base of Support (22.4 cm)', bbox: [810, 260, 970, 740], confidence: 0.92, category: 'motor', properties: { stance: 'broad', balance: 'compensated' } }
          ]
        },
        {
          timestamp: 3.2,
          label: 'Gait Initiation & Stance Phase',
          category: 'gait',
          confidence: 0.94,
          nodes: [
            { id: 'knee_bowing', label: 'Symmetrical Genu Varum (2.2 cm)', bbox: [600, 310, 860, 670], confidence: 0.93, category: 'orthopedic', properties: { symmetry: 'high', gap_cm: 2.2 } },
            { id: 'flatfoot_pad', label: 'Flexible Plantar Fat Pad', bbox: [830, 360, 980, 710], confidence: 0.89, category: 'motor', properties: { arch: 'physiologic fat pad' } }
          ]
        },
        {
          timestamp: 6.8,
          label: 'High-Guard Upper Limb Balance',
          category: 'motor',
          confidence: 0.95,
          nodes: [
            { id: 'toddler_arms', label: 'Bilateral High-Guard Balance', bbox: [240, 220, 490, 770], confidence: 0.95, category: 'motor', properties: { guard_posture: 'high-guard', stability: 'seeking' } },
            { id: 'anterior_pelvis', label: 'Anterior Pelvic Tilt (~16°)', bbox: [460, 320, 670, 630], confidence: 0.91, category: 'biomechanics', properties: { tilt_deg: 16.2 } }
          ]
        },
        {
          timestamp: 10.2,
          label: 'Weight Transfer & Terminal Stance',
          category: 'biomechanics',
          confidence: 0.92,
          nodes: [
            { id: 'dynamic_cop', label: 'Dynamic Center of Pressure', bbox: [770, 300, 960, 690], confidence: 0.90, category: 'biomechanics', properties: { trajectory: 'anterior-medial' } },
            { id: 'toddler_spine', label: 'Spinal Alignment (Compensated)', bbox: [330, 290, 610, 520], confidence: 0.93, category: 'biomechanics', properties: { plumb_shift: '5.8 mm' } }
          ]
        }
      ];
    }

    // Default agriculture foliar chlorosis and fenestration temporal keyframes
    return [
      {
        timestamp: 0.0,
        label: 'Canopy Overview & Apical Shoot',
        category: 'morphology',
        confidence: 0.97,
        nodes: [
          { id: 'apical_leaf', label: 'Emergent Juvenile Apical Shoot', bbox: [120, 350, 490, 690], confidence: 0.96, category: 'vegetative_vigor', properties: { turgor: 'high', meristem: 'active expansion' } },
          { id: 'leaf_fenestrations_01', label: 'Fenestrated Leaf Margin (PCD)', bbox: [260, 150, 720, 530], confidence: 0.97, category: 'morphology', properties: { mechanism: 'PCD apoptosis', pest_damage: 'None' } }
        ]
      },
      {
        timestamp: 3.5,
        label: 'Mid-Canopy Chlorosis Diagnostic',
        category: 'pathology',
        confidence: 0.95,
        nodes: [
          { id: 'chlorotic_zone', label: 'Interveinal Foliar Chlorosis', bbox: [210, 250, 630, 750], confidence: 0.96, category: 'pathology', properties: { pattern: 'interveinal yellowing', severity: 'moderate' } },
          { id: 'root_zone_emitter', label: 'Drip Emitter (Visible Saturation)', bbox: [700, 490, 920, 840], confidence: 0.94, category: 'infrastructure', properties: { type: 'drip emitter', status: 'soil visibly saturated' } }
        ]
      },
      {
        timestamp: 7.2,
        label: 'Petiole Turgor & Abaxial Stomata',
        category: 'physiology',
        confidence: 0.93,
        nodes: [
          { id: 'petiole_turgor', label: 'Petiole Angle Assessment', bbox: [390, 360, 760, 630], confidence: 0.93, category: 'physiology', properties: { posture: 'upright', turgor: 'adequate' } },
          { id: 'fruit_01', label: 'Apical Fruit Truss', bbox: [430, 100, 640, 340], confidence: 0.94, category: 'developmental', properties: { color: 'green/immature', cluster: 'apical' } }
        ]
      },
      {
        timestamp: 10.5,
        label: 'Root Substrate Aeration Diagnostic',
        category: 'substrate',
        confidence: 0.94,
        nodes: [
          { id: 'soil_drainage', label: 'Bark-Perlite Substrate', bbox: [580, 320, 970, 810], confidence: 0.92, category: 'substrate', properties: { texture: 'coarse chunky', drainage: 'visible perlite' } }
        ]
      }
    ];
  }, [isPediatrics]);

  // Compute active keyframe based on videoCurrentTime
  const activeKeyframe = useMemo(() => {
    if (!temporalKeyframes || temporalKeyframes.length === 0) return null;
    let selected = temporalKeyframes[0];
    let selectedIdx = 0;
    for (let i = 0; i < temporalKeyframes.length; i++) {
      if (videoCurrentTime >= temporalKeyframes[i].timestamp) {
        selected = temporalKeyframes[i];
        selectedIdx = i;
      }
    }
    return { ...selected, index: selectedIdx };
  }, [videoCurrentTime, temporalKeyframes]);

  // Handle play/pause simulation or HTML5 video synchronization
  useEffect(() => {
    let interval = null;
    if (isVideoPlaying) {
      interval = setInterval(() => {
        setVideoCurrentTime((prev) => {
          if (prev >= videoDuration) {
            setIsVideoPlaying(false);
            return 0;
          }
          return Number((prev + 0.1).toFixed(1));
        });
      }, 100);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isVideoPlaying, videoDuration]);

  // Sync HTML5 video element if loaded
  const handleVideoTimeUpdate = () => {
    if (videoRef.current) {
      setVideoCurrentTime(videoRef.current.currentTime);
      if (videoRef.current.duration && !isNaN(videoRef.current.duration)) {
        setVideoDuration(videoRef.current.duration);
      }
    }
  };

  const handlePlayToggle = () => {
    if (videoRef.current) {
      if (isVideoPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play().catch(() => {});
      }
    }
    setIsVideoPlaying(!isVideoPlaying);
  };

  const handleSeek = (newTime) => {
    setVideoCurrentTime(newTime);
    if (videoRef.current) {
      videoRef.current.currentTime = newTime;
    }
  };

  const handleSelectKeyframe = (index, kf) => {
    setActiveKeyframeIndex(index);
    handleSeek(kf.timestamp);
  };

  const displayImage =
    customImageData ||
    customImageUrl ||
    preset?.image ||
    null;

  // Unified upload dispatcher (supports both photos and video clips)
  const handleUpload = (fileDataOrFile, url) => {
    if (fileDataOrFile instanceof File) {
      const isVideo = fileDataOrFile.type.startsWith('video/') || /\.(mp4|mov|webm|avi|mkv)$/i.test(fileDataOrFile.name);
      if (isVideo) {
        const objectUrl = URL.createObjectURL(fileDataOrFile);
        setCustomVideoUrl(objectUrl);
        setMediaMode('video');
        return;
      }
    }
    if (url && (url.endsWith('.mp4') || url.endsWith('.webm') || url.includes('video'))) {
      setCustomVideoUrl(url);
      setMediaMode('video');
      return;
    }
    if (onImageUploaded) onImageUploaded(fileDataOrFile, url);
    if (fileDataOrFile && onUploadCustom) onUploadCustom(fileDataOrFile);
    if (url && onPasteUrl) onPasteUrl(url);
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleUpload(file, null);
    }
  };

  const handleUrlSubmit = (e) => {
    e.preventDefault();
    if (urlInput.trim()) {
      handleUpload(null, urlInput.trim());
      setShowUrlInput(false);
    }
  };

  // Dynamic tool mapping for any grounded node
  const getToolMapping = (nodeId) => {
    const nodeObj = (groundedNodes || []).find((n) => n.id === nodeId) || { id: nodeId, label: nodeId };
    return getDynamicToolMapping(nodeObj);
  };

  // Extract and normalize grounded nodes strictly from the active dataset payload
  const groundedNodes = useMemo(() => {
    // If in video mode, dynamically ground nodes to the active temporal keyframe
    if (mediaMode === 'video' && activeKeyframe && activeKeyframe.nodes) {
      return activeKeyframe.nodes.map((n) => ({
        ...n,
        bbox: n.bbox
      }));
    }

    const rawList = Array.isArray(nodes) ? nodes : [];
    return rawList
      .filter((n) => n && n.bbox && Array.isArray(n.bbox) && n.bbox.length === 4)
      .map((n) => {
        let [ymin, xmin, ymax, xmax] = n.bbox.map(Number);
        if (isNaN(ymin) || isNaN(xmin) || isNaN(ymax) || isNaN(xmax)) return null;

        const maxCoord = Math.max(ymin, xmin, ymax, xmax);

        // Auto-scale 0..1 normalized decimal coordinates to 0..1000 SVG coordinate system
        if (maxCoord <= 1.05) {
          ymin *= 1000;
          xmin *= 1000;
          ymax *= 1000;
          xmax *= 1000;
        }
        // Auto-scale 0..100 percentage coordinates to 0..1000
        else if (maxCoord <= 100) {
          ymin *= 10;
          xmin *= 10;
          ymax *= 10;
          xmax *= 10;
        }

        // Handle [xmin, ymin, width, height] format where ymax or xmax represents dimension
        if (ymax < ymin) ymax = ymin + ymax;
        if (xmax < xmin) xmax = xmin + xmax;

        // Ensure reasonable bounds within 1000x1000 coordinate space
        ymin = Math.max(0, Math.min(960, ymin));
        xmin = Math.max(0, Math.min(960, xmin));
        ymax = Math.max(ymin + 40, Math.min(1000, ymax));
        xmax = Math.max(xmin + 40, Math.min(1000, xmax));

        return {
          ...n,
          bbox: [Math.round(ymin), Math.round(xmin), Math.round(ymax), Math.round(xmax)]
        };
      })
      .filter(Boolean);
  }, [nodes, mediaMode, activeKeyframe]);

  // Synchronize visibleBoxIds when groundedNodes change (default: reveal all grounded anchors)
  useEffect(() => {
    if (groundedNodes && groundedNodes.length > 0) {
      setVisibleBoxIds(new Set(groundedNodes.map((n) => n.id)));
    } else {
      setVisibleBoxIds(new Set());
    }
  }, [groundedNodes]);

  // When an external node is selected (e.g. from the knowledge graph), ensure its rectangle is visible
  useEffect(() => {
    if (selectedNodeId && groundedNodes && groundedNodes.length > 0) {
      const match = groundedNodes.find(
        (n) =>
          n.id === selectedNodeId ||
          n.id.toLowerCase() === selectedNodeId.toLowerCase() ||
          n.label?.toLowerCase().includes(selectedNodeId.toLowerCase())
      );
      if (match) {
        setVisibleBoxIds((prev) => {
          const next = new Set(prev);
          next.add(match.id);
          return next;
        });
        setActiveHudNode(match);
      }
    }
  }, [selectedNodeId, groundedNodes]);

  const toggleBoxVisibility = (boxId) => {
    setVisibleBoxIds((prev) => {
      const next = new Set(prev);
      if (next.has(boxId)) {
        next.delete(boxId);
      } else {
        next.add(boxId);
      }
      return next;
    });
  };

  const showAllBoxes = () => {
    setVisibleBoxIds(new Set(groundedNodes.map((n) => n.id)));
  };

  const hideAllBoxes = () => {
    setVisibleBoxIds(new Set());
  };

  return (
    <div
      className="image-inspector-root custom-pane-scrollbar"
      style={{
        display: 'flex',
        flexDirection: 'column',
        width: '100%',
        minHeight: '100%',
        boxSizing: 'border-box'
      }}
    >
      {/* 1. Header Toolbar with Multimodal Mode Switcher */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.65rem', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{
            width: '28px',
            height: '28px',
            borderRadius: '6px',
            background: 'rgba(56, 189, 248, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            {mediaMode === 'video' ? (
              <Film size={15} color="var(--primary)" />
            ) : (
              <Camera size={15} color="var(--primary)" />
            )}
          </div>
          <div>
            <span style={{ fontWeight: '700', fontSize: '0.86rem', color: 'var(--text-main)' }}>
              {mediaMode === 'video' ? 'Temporal Video Grounding Engine' : 'Visual Evidence Grounding'}
            </span>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginLeft: '6px' }}>
              ({groundedNodes.length} active anchors)
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
          {/* Video mode indicator + reset (only visible when a video is loaded) */}
          {mediaMode === 'video' && (
            <button
              type="button"
              onClick={() => { setMediaMode('image'); setCustomVideoUrl(null); setIsVideoPlaying(false); setVideoCurrentTime(0); }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                padding: '0.22rem 0.5rem',
                borderRadius: '6px',
                background: 'rgba(56, 189, 248, 0.12)',
                border: '1px solid rgba(56, 189, 248, 0.35)',
                color: 'var(--primary)',
                fontSize: '0.68rem',
                fontWeight: 600,
                cursor: 'pointer'
              }}
              title="Exit video mode and return to photo inspection"
            >
              <Camera size={11} />
              <span>Back to Photo</span>
            </button>
          )}

          {/* Quick upload button (Accepts images and video clips — mode auto-detects) */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept="image/*,video/*"
            style={{ display: 'none' }}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '0.25rem 0.55rem',
              borderRadius: '6px',
              background: 'var(--bg-dark)',
              border: '1px solid var(--border-color)',
              fontSize: '0.72rem',
              color: 'var(--text-main)',
              cursor: 'pointer',
              fontWeight: 500
            }}
            title="Upload specimen photo or video clip"
          >
            <Upload size={12} />
            <span>Upload</span>
          </button>

          {/* Stream URL Toggle */}
          <button
            onClick={() => setShowUrlInput(!showUrlInput)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '0.25rem 0.55rem',
              borderRadius: '6px',
              background: showUrlInput ? 'rgba(56, 189, 248, 0.15)' : 'var(--bg-dark)',
              border: showUrlInput ? '1px solid var(--primary)' : '1px solid var(--border-color)',
              fontSize: '0.72rem',
              color: showUrlInput ? 'var(--primary)' : 'var(--text-main)',
              cursor: 'pointer',
              fontWeight: 500
            }}
            title="Load media from URL"
          >
            <LinkIcon size={12} />
            <span>URL</span>
          </button>

          {/* Bounding Box Master Toggle */}
          <button
            onClick={() => {
              if (visibleBoxIds.size > 0) {
                hideAllBoxes();
              } else {
                showAllBoxes();
              }
            }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '0.25rem 0.55rem',
              borderRadius: '6px',
              background: visibleBoxIds.size > 0 ? 'rgba(56, 189, 248, 0.12)' : 'var(--bg-dark)',
              border: visibleBoxIds.size > 0 ? '1px solid rgba(56, 189, 248, 0.4)' : '1px solid var(--border-color)',
              fontSize: '0.72rem',
              color: visibleBoxIds.size > 0 ? 'var(--primary)' : 'var(--text-muted)',
              cursor: 'pointer',
              fontWeight: 600
            }}
            title={visibleBoxIds.size > 0 ? 'Hide all bounding boxes' : 'Show all bounding boxes'}
          >
            {visibleBoxIds.size > 0 ? <Eye size={12} /> : <EyeOff size={12} />}
            <span>{visibleBoxIds.size > 0 ? `${visibleBoxIds.size} Visible` : 'All Hidden'}</span>
          </button>

          {onCloseCamera && (
            <button onClick={onCloseCamera} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '2px' }}>
              <X size={15} />
            </button>
          )}
        </div>
      </div>

      {/* URL Input Form */}
      {showUrlInput && (
        <form onSubmit={handleUrlSubmit} style={{ display: 'flex', gap: '0.4rem', marginBottom: '0.6rem' }}>
          <input
            type="url"
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            placeholder="Paste direct image or video URL (https://...)"
            style={{
              flex: 1,
              padding: '0.3rem 0.55rem',
              borderRadius: '6px',
              border: '1px solid var(--border-color)',
              background: 'var(--bg-dark)',
              color: 'var(--text-main)',
              fontSize: '0.76rem'
            }}
          />
          <button type="submit" className="btn btn-primary" style={{ padding: '0.3rem 0.65rem', fontSize: '0.75rem' }}>
            Load
          </button>
        </form>
      )}

      {/* 2. Visual Evidence Container (Photo or Video Player) */}
      <div style={{
        position: 'relative',
        width: '100%',
        minHeight: '260px',
        maxHeight: '440px',
        aspectRatio: '16 / 10',
        borderRadius: '10px',
        overflow: 'hidden',
        border: '1px solid var(--border-color)',
        background: '#090d16',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: '0 4px 16px rgba(0,0,0,0.25)'
      }}>
        {/* Media Rendering: Video or Image */}
        {mediaMode === 'video' ? (
          customVideoUrl ? (
            <video
              ref={videoRef}
              src={customVideoUrl}
              onTimeUpdate={handleVideoTimeUpdate}
              playsInline
              style={{ width: '100%', height: '100%', objectFit: 'contain' }}
            />
          ) : (
            // Animated simulated video canvas using active frame backdrop
            <div style={{ position: 'relative', width: '100%', height: '100%', overflow: 'hidden' }}>
              <img
                src={displayImage}
                alt="Temporal Video Keyframe"
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'contain',
                  filter: isVideoPlaying ? 'brightness(1.05)' : 'brightness(0.95)',
                  transition: 'filter 0.3s ease'
                }}
              />
              {/* Scanline / Live Video HUD Overlay */}
              <div
                style={{
                  position: 'absolute',
                  top: 8,
                  right: 8,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: 'rgba(0, 0, 0, 0.7)',
                  padding: '0.2rem 0.5rem',
                  borderRadius: '4px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.66rem',
                  color: '#38bdf8',
                  border: '1px solid rgba(56, 189, 248, 0.3)'
                }}
              >
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: isVideoPlaying ? '#38bdf8' : 'var(--text-muted)', boxShadow: isVideoPlaying ? '0 0 6px #38bdf8' : 'none' }} />
                <span>{isVideoPlaying ? 'PLAYING' : 'PAUSED'}</span>
                <span>•</span>
                <span>{videoCurrentTime.toFixed(1)}s / {videoDuration.toFixed(1)}s</span>
              </div>
            </div>
          )
        ) : displayImage ? (
          <img
            src={displayImage}
            alt="Visual Evidence"
            onError={(e) => {
              if (!e.target.src.includes('monstera_sample.png')) {
                e.target.src = '/monstera_sample.png';
              }
            }}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'contain',
              display: 'block'
            }}
          />
        ) : (
          <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
            <Camera size={32} style={{ opacity: 0.5, marginBottom: '0.4rem' }} />
            <div style={{ fontSize: '0.8rem' }}>No visual evidence loaded</div>
          </div>
        )}

        {/* SVG Bounding Boxes Overlay - Multi-box rendering based on visibleBoxIds & Video Keyframe */}
        {(displayImage || customVideoUrl) && groundedNodes.length > 0 && (
          <svg
            viewBox="0 0 1000 1000"
            preserveAspectRatio="none"
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              pointerEvents: 'none',
              zIndex: 5
            }}
          >
            <defs>
              <filter id="box-glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="6" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            {groundedNodes.map((node, idx) => {
              if (!visibleBoxIds.has(node.id)) return null;

              const color = ANCHOR_COLORS[idx % ANCHOR_COLORS.length];
              const [ymin, xmin, ymax, xmax] = node.bbox;
              const width = Math.max(30, xmax - xmin);
              const height = Math.max(30, ymax - ymin);
              const isSelected =
                (selectedNodeId &&
                  (node.id === selectedNodeId ||
                    node.id.toLowerCase() === selectedNodeId.toLowerCase() ||
                    node.label?.toLowerCase().includes(selectedNodeId.toLowerCase()))) ||
                (activeHudNode && activeHudNode.id === node.id);
              const isHovered = hoveredBoxId === node.id;
              const labelWidth = Math.min(Math.max(width, 130), 220);

              return (
                <g
                  key={node.id}
                  style={{ pointerEvents: 'auto', cursor: 'pointer', transition: 'all 0.15s ease-out' }}
                  onClick={(e) => {
                    e.stopPropagation();
                    const next = activeHudNode?.id === node.id ? null : node;
                    setActiveHudNode(next);
                    if (onSelectNode) onSelectNode(next ? node.id : null);
                  }}
                  onMouseEnter={() => setHoveredBoxId(node.id)}
                  onMouseLeave={() => setHoveredBoxId(null)}
                >
                  {/* Bounding Box Rectangle */}
                  <rect
                    x={xmin}
                    y={ymin}
                    width={width}
                    height={height}
                    rx="6"
                    fill={
                      isSelected
                        ? color.fill.replace('0.18', '0.35')
                        : isHovered
                        ? color.fill.replace('0.18', '0.26')
                        : color.fill
                    }
                    stroke={isSelected ? '#ffffff' : color.stroke}
                    strokeWidth={isSelected ? 3.5 : isHovered ? 2.8 : 2}
                    strokeDasharray={isSelected ? '7,3' : 'none'}
                    filter={isSelected || isHovered ? 'url(#box-glow)' : 'none'}
                  />

                  {/* Corner Target Reticles */}
                  {isSelected && (
                    <>
                      <circle cx={xmin} cy={ymin} r="4.5" fill={color.stroke} stroke="#ffffff" strokeWidth="1.5" />
                      <circle cx={xmax} cy={ymin} r="4.5" fill={color.stroke} stroke="#ffffff" strokeWidth="1.5" />
                      <circle cx={xmin} cy={ymax} r="4.5" fill={color.stroke} stroke="#ffffff" strokeWidth="1.5" />
                      <circle cx={xmax} cy={ymax} r="4.5" fill={color.stroke} stroke="#ffffff" strokeWidth="1.5" />
                    </>
                  )}

                  {/* Compact Grounded Entity Badge */}
                  <g transform={`translate(${xmin}, ${Math.max(6, ymin - 26)})`}>
                    <rect
                      x="0"
                      y="0"
                      width={labelWidth}
                      height="24"
                      rx="5"
                      fill={isSelected ? color.stroke : isHovered ? 'rgba(15, 23, 42, 0.95)' : 'rgba(15, 23, 42, 0.88)'}
                      stroke={color.stroke}
                      strokeWidth="1.2"
                    />

                    <circle cx="12" cy="12" r="4.5" fill={isSelected ? '#ffffff' : color.stroke} />
                    <text
                      x="22"
                      y="16"
                      fill={isSelected ? '#0f172a' : '#ffffff'}
                      fontSize="11px"
                      fontFamily="Outfit, sans-serif"
                      fontWeight="600"
                    >
                      {node.label.length > 22 ? node.label.substring(0, 20) + '…' : node.label}
                    </text>
                  </g>
                </g>
              );
            })}
          </svg>
        )}

        {/* Minimal subtle bottom bar */}
        <div style={{
          position: 'absolute',
          bottom: 6,
          left: 8,
          right: 8,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'rgba(0, 0, 0, 0.65)',
          backdropFilter: 'blur(6px)',
          padding: '0.25rem 0.6rem',
          borderRadius: '5px',
          color: '#ffffff',
          fontSize: '0.68rem',
          zIndex: 10,
          pointerEvents: 'none'
        }}>
          <span style={{ fontWeight: 500, opacity: 0.9 }}>
            {mediaMode === 'video' ? `Keyframe @ ${videoCurrentTime.toFixed(1)}s: ${activeKeyframe?.label || 'Continuous Track'}` : preset?.title || "Visual Evidence"}
          </span>
          <span style={{ fontFamily: 'var(--font-mono)', color: visibleBoxIds.size > 0 ? 'var(--primary)' : 'var(--text-muted)' }}>
            {visibleBoxIds.size} of {groundedNodes.length} Rectangles Active
          </span>
        </div>
      </div>

      {/* 3. Interactive Video Timeline Scrubber (Rendered when in Video Mode) */}
      {mediaMode === 'video' && (
        <VideoTimelineScrubber
          currentTime={videoCurrentTime}
          duration={videoDuration}
          isPlaying={isVideoPlaying}
          onPlayToggle={handlePlayToggle}
          onSeek={handleSeek}
          keyframes={temporalKeyframes}
          activeKeyframeIndex={activeKeyframe?.index || 0}
          onSelectKeyframe={handleSelectKeyframe}
          fps={2.0}
        />
      )}

      {/* 4. Dedicated Inspector Card (Rendered cleanly below the media container) */}
      {activeHudNode && (
        <div
          className="animate-fade-in"
          style={{
            marginTop: '0.75rem',
            background: 'var(--bg-dark)',
            border: '1px solid rgba(56, 189, 248, 0.4)',
            borderRadius: '10px',
            padding: '0.75rem 0.85rem',
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.08)'
          }}
        >
          {/* Card Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <div style={{
                width: '26px',
                height: '26px',
                borderRadius: '6px',
                background: 'rgba(56, 189, 248, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--primary)'
              }}>
                <Zap size={14} />
              </div>
              <div>
                <div style={{ fontWeight: '700', fontSize: '0.86rem', color: 'var(--text-main)', lineHeight: 1.2 }}>
                  {activeHudNode.label}
                </div>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px', marginTop: '2px' }}>
                  <span style={{ textTransform: 'uppercase', fontWeight: 600, color: 'var(--primary)' }}>
                    {activeHudNode.category || 'entity'}
                  </span>
                  <span>•</span>
                  <span style={{ color: 'var(--primary)', fontFamily: 'var(--font-mono)' }}>
                    {Math.round((activeHudNode.confidence || 0.9) * 100)}% Confidence
                  </span>
                </div>
              </div>
            </div>

            <button
              onClick={() => setActiveHudNode(null)}
              style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '3px' }}
              title="Close inspection card"
            >
              <X size={15} />
            </button>
          </div>

          {/* Properties / Attributes Row */}
          {activeHudNode.properties && Object.keys(activeHudNode.properties).length > 0 && (
            <div style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '0.35rem',
              marginBottom: '0.6rem'
            }}>
              {Object.entries(activeHudNode.properties).slice(0, 4).map(([k, v]) => (
                <div
                  key={k}
                  style={{
                    background: 'rgba(56, 189, 248, 0.08)',
                    border: '1px solid rgba(56, 189, 248, 0.2)',
                    borderRadius: '5px',
                    padding: '0.2rem 0.45rem',
                    fontSize: '0.68rem',
                    fontFamily: 'var(--font-mono)',
                    display: 'flex',
                    gap: '4px'
                  }}
                >
                  <span style={{ color: 'var(--text-muted)' }}>{k.replace(/_/g, ' ')}:</span>
                  <span style={{ color: 'var(--primary)', fontWeight: 600 }}>{String(v)}</span>
                </div>
              ))}
            </div>
          )}

          {/* Action Row */}
          <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
            <button
              className="btn btn-primary"
              onClick={() => {
                const mapping = getToolMapping(activeHudNode.id);
                if (onOpenTool) onOpenTool(mapping.toolId, activeHudNode);
                setActiveHudNode(null);
              }}
              style={{
                flex: 2,
                fontSize: '0.74rem',
                padding: '0.4rem 0.6rem',
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '5px'
              }}
            >
              <Sparkles size={13} />
              <span>Launch {getToolMapping(activeHudNode.id).toolName}</span>
            </button>

            <button
              className="btn btn-secondary"
              onClick={() => {
                const mapping = getToolMapping(activeHudNode.id);
                if (onAskQuery) onAskQuery(mapping.suggestedQuery || `Analyze the physical implications of ${activeHudNode.label}`);
                setActiveHudNode(null);
              }}
              style={{
                flex: 1,
                fontSize: '0.72rem',
                padding: '0.4rem 0.5rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '4px'
              }}
            >
              <Crosshair size={12} color="var(--primary)" />
              <span>Ask SAAR</span>
            </button>

            <button
              className="btn btn-secondary"
              onClick={() => {
                if (onOpenGlossary) onOpenGlossary(activeHudNode.label);
                setActiveHudNode(null);
              }}
              style={{
                fontSize: '0.72rem',
                padding: '0.4rem 0.55rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '4px'
              }}
            >
              <Layers size={12} color="var(--primary)" />
              <span>Glossary</span>
            </button>
          </div>
        </div>
      )}

      {/* 5. Domain Specialist Navigation Tabs */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        marginTop: '0.85rem',
        borderBottom: '1px solid var(--border-color)',
        paddingBottom: '0.4rem'
      }}>
        <button
          type="button"
          onClick={() => setActiveSpecialistTab('anchors')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '5px',
            padding: '0.35rem 0.7rem',
            borderRadius: '6px',
            background: activeSpecialistTab === 'anchors' ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
            border: activeSpecialistTab === 'anchors' ? '1px solid rgba(56, 189, 248, 0.4)' : '1px solid transparent',
            color: activeSpecialistTab === 'anchors' ? 'var(--primary)' : 'var(--text-muted)',
            fontSize: '0.74rem',
            fontWeight: activeSpecialistTab === 'anchors' ? 700 : 500,
            cursor: 'pointer'
          }}
        >
          <Target size={13} />
          <span>Visual Anchors ({groundedNodes.length})</span>
        </button>

        {isAgriculture && (
          <button
            type="button"
            onClick={() => setActiveSpecialistTab('plantCare')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              padding: '0.35rem 0.7rem',
              borderRadius: '6px',
              background: activeSpecialistTab === 'plantCare' ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
              border: activeSpecialistTab === 'plantCare' ? '1px solid rgba(56, 189, 248, 0.4)' : '1px solid transparent',
              color: activeSpecialistTab === 'plantCare' ? 'var(--primary)' : 'var(--text-muted)',
              fontSize: '0.74rem',
              fontWeight: activeSpecialistTab === 'plantCare' ? 700 : 500,
              cursor: 'pointer'
            }}
          >
            <Sprout size={13} />
            <span>Botanical Care & Treatment Plan</span>
          </button>
        )}

        {isPediatrics && (
          <button
            type="button"
            onClick={() => setActiveSpecialistTab('toddlerPosture')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              padding: '0.35rem 0.7rem',
              borderRadius: '6px',
              background: activeSpecialistTab === 'toddlerPosture' ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
              border: activeSpecialistTab === 'toddlerPosture' ? '1px solid rgba(56, 189, 248, 0.4)' : '1px solid transparent',
              color: activeSpecialistTab === 'toddlerPosture' ? 'var(--primary)' : 'var(--text-muted)',
              fontSize: '0.74rem',
              fontWeight: activeSpecialistTab === 'toddlerPosture' ? 700 : 500,
              cursor: 'pointer'
            }}
          >
            <Activity size={13} />
            <span>Toddler Posture & Screening</span>
          </button>
        )}
      </div>

      {/* 6. Active Tab Pane Content */}
      {activeSpecialistTab === 'plantCare' && isAgriculture && (
        <PlantCareCard
          presetId={presetId}
          onAskAgronomist={(q) => onAskQuery && onAskQuery(q)}
        />
      )}

      {activeSpecialistTab === 'toddlerPosture' && isPediatrics && (
        <ToddlerPostureCard
          presetId={presetId}
          onAskSpecialist={(q) => onAskQuery && onAskQuery(q)}
        />
      )}

      {activeSpecialistTab === 'anchors' && groundedNodes.length > 0 && (
        <div style={{ marginTop: '0.65rem' }}>
          {/* Section Header with Bulk Actions & Guidance */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '0.5rem',
            flexWrap: 'wrap',
            gap: '0.5rem',
            padding: '0 0.1rem'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontWeight: 700, fontSize: '0.8rem', color: 'var(--text-main)' }}>
                Regional Bounding Box Directory
              </span>
              <span style={{
                fontSize: '0.68rem',
                fontFamily: 'var(--font-mono)',
                padding: '0.12rem 0.45rem',
                borderRadius: '10px',
                background: visibleBoxIds.size > 0 ? 'rgba(56, 189, 248, 0.12)' : 'rgba(255, 255, 255, 0.05)',
                color: visibleBoxIds.size > 0 ? 'var(--primary)' : 'var(--text-muted)',
                fontWeight: 600,
                border: visibleBoxIds.size > 0 ? '1px solid rgba(56, 189, 248, 0.35)' : '1px solid var(--border-color)'
              }}>
                {visibleBoxIds.size} of {groundedNodes.length} visible
              </span>
            </div>

            {/* Quick Bulk Action Buttons */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <button
                type="button"
                onClick={showAllBoxes}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '0.22rem 0.55rem',
                  borderRadius: '6px',
                  background: visibleBoxIds.size === groundedNodes.length ? 'rgba(56, 189, 248, 0.15)' : 'var(--bg-dark)',
                  border: '1px solid var(--border-color)',
                  color: visibleBoxIds.size === groundedNodes.length ? 'var(--primary)' : 'var(--text-main)',
                  fontSize: '0.7rem',
                  fontWeight: 500,
                  cursor: 'pointer'
                }}
                title="Display all bounding boxes on the media canvas"
              >
                <Eye size={12} />
                <span>Show All</span>
              </button>

              <button
                type="button"
                onClick={hideAllBoxes}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '0.22rem 0.55rem',
                  borderRadius: '6px',
                  background: visibleBoxIds.size === 0 ? 'rgba(255, 255, 255, 0.08)' : 'var(--bg-dark)',
                  border: '1px solid var(--border-color)',
                  color: visibleBoxIds.size === 0 ? 'var(--text-main)' : 'var(--text-muted)',
                  fontSize: '0.7rem',
                  fontWeight: 500,
                  cursor: 'pointer'
                }}
                title="Hide all bounding boxes for an unobstructed view"
              >
                <EyeOff size={12} />
                <span>Hide All</span>
              </button>
            </div>
          </div>

          <div style={{ fontSize: '0.71rem', color: 'var(--text-muted)', marginBottom: '0.65rem' }}>
            Click any label card to toggle its rectangle on/off on the canvas. Multiple rectangles can be viewed simultaneously.
          </div>

          {/* Cards Grid */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
            gap: '0.6rem',
            paddingBottom: '2.5rem'
          }}>
            {groundedNodes.length === 0 ? (
              <div style={{
                gridColumn: '1 / -1',
                padding: '1.5rem',
                textAlign: 'center',
                color: 'var(--text-muted)',
                background: 'rgba(255, 255, 255, 0.02)',
                borderRadius: '8px',
                border: '1px dashed var(--border-color)',
                fontSize: '0.78rem'
              }}>
                <Crosshair size={24} style={{ opacity: 0.4, margin: '0 auto 0.5rem auto' }} />
                <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>No visual bounding boxes detected</div>
                <div style={{ fontSize: '0.72rem', opacity: 0.7 }}>
                  Visual anchors appear when an image is analyzed by the perception layer.
                </div>
              </div>
            ) : (
              groundedNodes.map((node, idx) => {
                const color = ANCHOR_COLORS[idx % ANCHOR_COLORS.length];
                const isVisible = visibleBoxIds.has(node.id);
                const isHovered = hoveredBoxId === node.id;
                const mapping = getToolMapping(node.id);

                return (
                <div
                  key={node.id}
                  onClick={() => {
                    toggleBoxVisibility(node.id);
                    if (!isVisible) {
                      setActiveHudNode(node);
                      if (onSelectNode) onSelectNode(node.id);
                    }
                  }}
                  onMouseEnter={() => setHoveredBoxId(node.id)}
                  onMouseLeave={() => setHoveredBoxId(null)}
                  style={{
                    borderRadius: '9px',
                    border: isVisible
                      ? `1.5px solid ${color.stroke}`
                      : isHovered
                      ? '1px solid rgba(255, 255, 255, 0.25)'
                      : '1px solid var(--border-color)',
                    background: isVisible
                      ? 'rgba(15, 23, 42, 0.82)'
                      : 'rgba(15, 23, 42, 0.4)',
                    boxShadow: isVisible
                      ? `0 4px 14px ${color.glow}`
                      : 'none',
                    padding: '0.65rem 0.75rem',
                    cursor: 'pointer',
                    transition: 'all 0.18s cubic-bezier(0.4, 0, 0.2, 1)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.45rem',
                    position: 'relative',
                    overflow: 'hidden'
                  }}
                >
                  {/* Top accent line when rectangle is visible */}
                  {isVisible && (
                    <div style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      height: '2.5px',
                      background: color.stroke,
                      boxShadow: `0 0 8px ${color.stroke}`
                    }} />
                  )}

                  {/* Card Top Row: Color indicator dot, Title, and Toggle pill */}
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '7px', minWidth: 0 }}>
                      <span
                        style={{
                          width: '10px',
                          height: '10px',
                          minWidth: '10px',
                          borderRadius: '50%',
                          background: isVisible ? color.stroke : 'var(--text-muted)',
                          boxShadow: isVisible ? `0 0 7px ${color.stroke}` : 'none',
                          transition: 'all 0.15s ease'
                        }}
                      />
                      <span
                        style={{
                          fontWeight: 700,
                          fontSize: '0.83rem',
                          color: isVisible ? '#ffffff' : 'var(--text-muted)',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis'
                        }}
                        title={node.label}
                      >
                        {node.label}
                      </span>
                    </div>

                    {/* Toggle State Pill */}
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        padding: '0.2rem 0.45rem',
                        borderRadius: '10px',
                        fontSize: '0.66rem',
                        fontWeight: 600,
                        background: isVisible ? color.bg : 'rgba(255, 255, 255, 0.04)',
                        border: isVisible ? `1px solid ${color.border}` : '1px solid var(--border-color)',
                        color: isVisible ? color.text : 'var(--text-muted)',
                        flexShrink: 0,
                        transition: 'all 0.15s ease'
                      }}
                    >
                      {isVisible ? <Eye size={11} /> : <EyeOff size={11} />}
                      <span>{isVisible ? 'ON' : 'OFF'}</span>
                    </div>
                  </div>

                  {/* Card Sub-row: Category badge, Confidence % and Dimensions */}
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.68rem', gap: '4px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                      <span style={{
                        textTransform: 'uppercase',
                        fontWeight: 600,
                        fontSize: '0.62rem',
                        padding: '0.1rem 0.35rem',
                        borderRadius: '4px',
                        background: 'rgba(255, 255, 255, 0.06)',
                        color: 'var(--text-muted)'
                      }}>
                        {node.category || 'feature'}
                      </span>
                      <span style={{
                        color: 'var(--primary)',
                        fontFamily: 'var(--font-mono)',
                        fontWeight: 600
                      }}>
                        {Math.round((node.confidence || 0.9) * 100)}% Conf.
                      </span>
                    </div>

                    <span style={{ color: 'var(--text-muted)', fontSize: '0.62rem', fontFamily: 'var(--font-mono)', opacity: 0.8 }}>
                      pos: {Math.round(node.bbox[1] / 10)}%,{Math.round(node.bbox[0] / 10)}% · {Math.max(1, Math.round((node.bbox[3] - node.bbox[1]) / 10))}×{Math.max(1, Math.round((node.bbox[2] - node.bbox[0]) / 10))}%
                    </span>
                  </div>

                  {/* Optional Properties preview */}
                  {node.properties && Object.keys(node.properties).length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '3px', marginTop: '1px' }}>
                      {Object.entries(node.properties).slice(0, 2).map(([k, v]) => (
                        <span
                          key={k}
                          style={{
                            fontSize: '0.63rem',
                            padding: '0.1rem 0.35rem',
                            borderRadius: '3px',
                            background: 'rgba(255, 255, 255, 0.04)',
                            color: 'var(--text-muted)',
                            fontFamily: 'var(--font-mono)'
                          }}
                        >
                          {k.replace(/_/g, ' ')}: <strong style={{ color: isVisible ? color.text : 'var(--text-main)' }}>{String(v)}</strong>
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Card Action Buttons */}
                  <div
                    style={{
                      display: 'flex',
                      gap: '4px',
                      marginTop: '2px',
                      paddingTop: '0.35rem',
                      borderTop: '1px solid rgba(255, 255, 255, 0.05)'
                    }}
                    onClick={(e) => e.stopPropagation()}
                  >
                    <button
                      type="button"
                      onClick={() => {
                        if (onOpenTool) onOpenTool(mapping.toolId, node);
                      }}
                      style={{
                        flex: 2,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '3px',
                        padding: '0.25rem 0.45rem',
                        borderRadius: '5px',
                        background: isVisible ? 'rgba(56, 189, 248, 0.12)' : 'var(--bg-dark)',
                        border: isVisible ? '1px solid rgba(56, 189, 248, 0.35)' : '1px solid var(--border-color)',
                        color: isVisible ? 'var(--primary)' : 'var(--text-muted)',
                        fontSize: '0.68rem',
                        fontWeight: 600,
                        cursor: 'pointer'
                      }}
                      title={`Launch ${mapping.toolName}`}
                    >
                      <Sparkles size={11} />
                      <span>{mapping.actionLabel?.split(' ')[0] || 'Analyze'}</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        if (onAskQuery) onAskQuery(mapping.suggestedQuery || `Analyze ${node.label}`);
                      }}
                      style={{
                        flex: 1,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '3px',
                        padding: '0.25rem 0.45rem',
                        borderRadius: '5px',
                        background: 'var(--bg-dark)',
                        border: '1px solid var(--border-color)',
                        color: 'var(--text-main)',
                        fontSize: '0.68rem',
                        cursor: 'pointer'
                      }}
                      title="Ask SAAR Chat about this region"
                    >
                      <Crosshair size={11} color="var(--primary)" />
                      <span>Ask</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        if (onOpenGlossary) onOpenGlossary(node.label);
                      }}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        padding: '0.25rem 0.45rem',
                        borderRadius: '5px',
                        background: 'var(--bg-dark)',
                        border: '1px solid var(--border-color)',
                        color: 'var(--text-muted)',
                        fontSize: '0.68rem',
                        cursor: 'pointer'
                      }}
                      title="Open Glossary Definition"
                    >
                      <Layers size={11} color="var(--primary)" />
                    </button>
                  </div>
                </div>
              );
            }))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ImageInspector;
