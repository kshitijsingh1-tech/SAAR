import React, { useState, useRef, useMemo, useEffect } from 'react';
import {
  Eye, EyeOff, Radio, Upload, Sparkles, Link as LinkIcon,
  Camera, X, Crosshair, Target, Layers, Droplets,
  HelpCircle, ExternalLink, Zap, Check, Film, Play, Pause,
  RotateCcw, AlertCircle, ArrowRight, MessageSquare
} from 'lucide-react';
import { VideoTimelineScrubber } from './VideoTimelineScrubber';

// Semantic biological & physical color palette for anatomical organs
const SEMANTIC_ORGAN_COLORS = {
  petals_blooms: {
    stroke: '#f43f5e', // Vibrant rose red / coral
    fill: 'rgba(244, 63, 94, 0.22)',
    glow: 'rgba(244, 63, 94, 0.45)',
    text: '#f43f5e',
    bg: 'rgba(244, 63, 94, 0.1)',
    border: 'rgba(244, 63, 94, 0.45)'
  },
  leaves_foliage: {
    stroke: '#10b981', // Vibrant emerald green
    fill: 'rgba(16, 185, 129, 0.2)',
    glow: 'rgba(16, 185, 129, 0.4)',
    text: '#10b981',
    bg: 'rgba(16, 185, 129, 0.1)',
    border: 'rgba(16, 185, 129, 0.45)'
  },
  stems_shoots: {
    stroke: '#f59e0b', // Vibrant amber
    fill: 'rgba(245, 158, 11, 0.2)',
    glow: 'rgba(245, 158, 11, 0.4)',
    text: '#f59e0b',
    bg: 'rgba(245, 158, 11, 0.1)',
    border: 'rgba(245, 158, 11, 0.45)'
  },
  root_system: {
    stroke: '#d97706', // Deep earthy ochre
    fill: 'rgba(217, 119, 6, 0.2)',
    glow: 'rgba(217, 119, 6, 0.4)',
    text: '#d97706',
    bg: 'rgba(217, 119, 6, 0.1)',
    border: 'rgba(217, 119, 6, 0.45)'
  },
  fruit_cluster: {
    stroke: '#fb7185', // Rose coral
    fill: 'rgba(251, 113, 133, 0.2)',
    glow: 'rgba(251, 113, 133, 0.4)',
    text: '#fb7185',
    bg: 'rgba(251, 113, 133, 0.1)',
    border: 'rgba(251, 113, 133, 0.45)'
  },
  telemetry_sensor: {
    stroke: '#06b6d4', // Cyan probe
    fill: 'rgba(6, 182, 212, 0.2)',
    glow: 'rgba(6, 182, 212, 0.4)',
    text: '#06b6d4',
    bg: 'rgba(6, 182, 212, 0.1)',
    border: 'rgba(6, 182, 212, 0.45)'
  },
  pathology_site: {
    stroke: '#ef4444', // Red warning
    fill: 'rgba(239, 68, 68, 0.22)',
    glow: 'rgba(239, 68, 68, 0.45)',
    text: '#ef4444',
    bg: 'rgba(239, 68, 68, 0.1)',
    border: 'rgba(239, 68, 68, 0.45)'
  },
  general: {
    stroke: '#0284c7', // Sky blue default
    fill: 'rgba(2, 132, 199, 0.2)',
    glow: 'rgba(2, 132, 199, 0.4)',
    text: '#0284c7',
    bg: 'rgba(2, 132, 199, 0.1)',
    border: 'rgba(2, 132, 199, 0.45)'
  }
};

const ANCHOR_COLORS = [
  SEMANTIC_ORGAN_COLORS.general,
  SEMANTIC_ORGAN_COLORS.leaves_foliage,
  SEMANTIC_ORGAN_COLORS.petals_blooms,
  SEMANTIC_ORGAN_COLORS.stems_shoots,
  SEMANTIC_ORGAN_COLORS.telemetry_sensor,
  SEMANTIC_ORGAN_COLORS.pathology_site
];

// Generic semantic mapping of visual entities to friendly user suggestions and analytical tools
const getDynamicToolMapping = (node) => {
  if (!node) return null;
  const category = String(node.category || '').toLowerCase();
  const label = String(node.label || node.id || '').toLowerCase();

  // 1. Plant Pathology, Chlorosis, Necrosis, Lesions
  if (category.includes('patholog') || label.includes('chloros') || label.includes('lesion') || label.includes('burn') || label.includes('stain') || label.includes('necros') || label.includes('blight')) {
    return {
      toolId: 'analytics',
      toolName: 'Pathology & Foliar Health Analyzer',
      fieldTopic: 'plant pathology & chlorosis',
      userSuggestion: 'Want to analyze foliar disease, chlorosis, or tissue discoloration?',
      actionText: 'Analyze Foliar Health',
      suggestedQuery: `Analyze the tissue pathology, discoloration patterns, and chlorosis severity for ${node.label || node.id}.`
    };
  }

  // 2. Vegetative Propagation, Cutting, Scion, Rooting, Callus, Aloe Medium
  if (category.includes('propagation') || category.includes('rhizogen') || label.includes('root') || label.includes('cutting') || label.includes('scion') || label.includes('callus') || label.includes('aloe') || label.includes('bloom') || label.includes('bud')) {
    return {
      toolId: 'grounded',
      toolName: 'Propagation & Rooting Evaluator',
      fieldTopic: 'vegetative propagation & rooting',
      userSuggestion: 'Want to evaluate cutting viability and rooting health for this field?',
      actionText: 'Explore Propagation Analysis',
      suggestedQuery: `Evaluate the cut geometry, rooting vitality, and propagation viability for ${node.label || node.id}.`
    };
  }

  // 3. Leaf Morphology, Fenestrations, Shoot, Foliar Structure
  if (category.includes('morpholog') || label.includes('fenestrat') || label.includes('apex') || label.includes('shoot') || label.includes('leaf') || label.includes('margin') || label.includes('foliage')) {
    return {
      toolId: 'grounded',
      toolName: 'Morphology & Growth Profiler',
      fieldTopic: 'plant morphology & growth vigor',
      userSuggestion: 'Want to examine leaf shape, developmental vigor, and structure?',
      actionText: 'Inspect Growth Structure',
      suggestedQuery: `Examine the anatomical structure and developmental vigor of ${node.label || node.id}.`
    };
  }

  // 4. Civil Infrastructure, Road, Pavement, Cracks, Cavities, Pipes, Drains
  if (category.includes('infrastruct') || category.includes('structur') || category.includes('obstacle') || label.includes('road') || label.includes('crack') || label.includes('pipe') || label.includes('drain') || label.includes('emitter') || label.includes('asphalt') || label.includes('void')) {
    return {
      toolId: 'analytics',
      toolName: 'Structural Integrity & Void Analyzer',
      fieldTopic: 'structural integrity & pavement wear',
      userSuggestion: 'Want to assess pavement cracking, void risks, or drainage wear?',
      actionText: 'Inspect Structural Data',
      suggestedQuery: `Assess the failure risk, load fatigue, and void progression affecting ${node.label || node.id}.`
    };
  }

  // 5. Biomechanics, Pediatric Gait, Posture, Lordosis, Bowing, Kinematics
  if (category.includes('biomechan') || category.includes('orthoped') || category.includes('postur') || category.includes('motor') || label.includes('lordosis') || label.includes('gait') || label.includes('stance') || label.includes('bowing')) {
    return {
      toolId: 'gait',
      toolName: 'Gait & Postural Alignment Screener',
      fieldTopic: 'gait kinematics & motor posture',
      userSuggestion: 'Want to screen toddler walking alignment and joint kinematics?',
      actionText: 'Open Gait Screening',
      suggestedQuery: `Evaluate the biomechanical angles, weight distribution, and developmental alignment of ${node.label || node.id}.`
    };
  }

  // 6. Environmental Telemetry, Sensors, Probes, Meters, Moisture, pH
  if (category.includes('measure') || category.includes('telemetry') || label.includes('sensor') || label.includes('probe') || label.includes('meter') || label.includes('moisture') || label.includes('ph')) {
    return {
      toolId: 'analytics',
      toolName: 'Environmental Sensor Profiler',
      fieldTopic: 'sensor readings & environmental trends',
      userSuggestion: 'Want to examine environmental sensor readings and trend thresholds?',
      actionText: 'View Sensor Analytics',
      suggestedQuery: `Evaluate the sensor telemetry, threshold exceedances, and environmental trends for ${node.label || node.id}.`
    };
  }

  // 7. General / Unspecified Visual Entity
  return {
    toolId: 'grounded',
    toolName: 'Evidence & Causal Graph Inspector',
    fieldTopic: 'evidence graph & relationships',
    userSuggestion: 'Want to analyze this region in the evidence graph?',
    actionText: 'Inspect in Evidence Graph',
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
  onOpenGlossary,
  domain = 'agriculture',
  investigationData = null
}) => {
  const [urlInput, setUrlInput] = useState('');
  const [showUrlInput, setShowUrlInput] = useState(false);
  const [visibleBoxIds, setVisibleBoxIds] = useState(() => new Set());
  const [hoveredBoxId, setHoveredBoxId] = useState(null);
  const [annotationMode, setAnnotationMode] = useState('callouts'); // 'callouts' (Diagram with Leader Lines) | 'boxes' (Traditional BBoxes)
  const fileInputRef = useRef(null);
  const imageContainerRef = useRef(null);
  const [contextMenu, setContextMenu] = useState(null); // { x: number, y: number, node: object | null }

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

  // Dynamic temporal keyframe streams strictly from backend video perception payload
  const temporalKeyframes = useMemo(() => {
    if (Array.isArray(preset?.keyframes) && preset.keyframes.length > 0) {
      return preset.keyframes;
    }
    return [];
  }, [preset]);


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
    investigationData?.imageData ||
    investigationData?.image_url ||
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

  // Derive textbook anatomical callouts leading out of the image into the margins (matching botanical anatomical diagrams)
  const anatomicalCallouts = useMemo(() => {
    if (!groundedNodes || groundedNodes.length === 0) return [];

    let candidates = [];

    // If 8 or fewer grounded features, treat each distinct object as its own individual callout (like textbook diagrams)
    if (groundedNodes.length <= 8) {
      candidates = groundedNodes.map((node, idx) => {
        let focalY = Math.round((node.bbox[0] + node.bbox[2]) / 2);
        let focalX = Math.round((node.bbox[1] + node.bbox[3]) / 2);
        if (Array.isArray(node.properties?.focal_point) && node.properties.focal_point.length === 2) {
          focalX = node.properties.focal_point[0];
          focalY = node.properties.focal_point[1];
        }

        const organ = (node.properties?.organ || '').toLowerCase();
        const cat = (node.category || '').toLowerCase();
        const labelLower = (node.label || '').toLowerCase();

        // Semantic color
        let color = ANCHOR_COLORS[idx % ANCHOR_COLORS.length];
        if (organ.includes('bloom') || organ.includes('flower') || labelLower.includes('bloom') || labelLower.includes('rose')) {
          color = SEMANTIC_ORGAN_COLORS.petals_blooms || color;
        } else if (organ.includes('leaf') || labelLower.includes('leaf') || labelLower.includes('foliage') || labelLower.includes('canopy')) {
          color = SEMANTIC_ORGAN_COLORS.leaves_foliage || color;
        } else if (organ.includes('stem') || labelLower.includes('stem') || labelLower.includes('shoot') || labelLower.includes('branch')) {
          color = SEMANTIC_ORGAN_COLORS.stems_shoots || color;
        } else if (organ.includes('root') || labelLower.includes('root') || labelLower.includes('substrate') || labelLower.includes('pot') || labelLower.includes('soil')) {
          color = SEMANTIC_ORGAN_COLORS.root_system || color;
        } else if (cat.includes('measurement') || labelLower.includes('sensor')) {
          color = SEMANTIC_ORGAN_COLORS.telemetry_sensor || color;
        } else if (cat.includes('pathology') || labelLower.includes('lesion')) {
          color = SEMANTIC_ORGAN_COLORS.pathology_site || color;
        }

        const naturalLeft = focalX < 500;
        const clearance = naturalLeft ? focalX : 1000 - focalX;

        // Parse clean title and subtitle (strip noisy parentheses or count strings)
        const rawLabel = node.label || 'Anatomical Feature';
        let mainTitle = rawLabel;
        let subtitle = node.properties?.phenological_stage || node.properties?.condition || node.category || 'morphology';

        const parenMatch = rawLabel.match(/^([^()]+)\s*\(([^)]+)\)$/);
        if (parenMatch) {
          mainTitle = parenMatch[1].trim();
          subtitle = parenMatch[2].split(' - ')[0].trim();
        } else if (rawLabel.includes(' & ')) {
          const parts = rawLabel.split(' & ');
          mainTitle = parts[0].trim();
          subtitle = parts[1].trim();
        }

        // Determine anatomical system (Shoot System vs Root System) for grouping brackets
        let systemName = 'Shoot System';
        if (organ.includes('root') || labelLower.includes('root') || labelLower.includes('substrate') || labelLower.includes('soil') || labelLower.includes('pot')) {
          systemName = 'Root System';
        } else if (cat.includes('measurement') || labelLower.includes('sensor')) {
          systemName = 'Sensor Network';
        } else if (cat.includes('pathology') || labelLower.includes('lesion')) {
          systemName = 'Pathology Sites';
        }

        return {
          id: node.id,
          key: node.id,
          title: mainTitle,
          subtitle,
          systemName,
          node,
          primaryNode: node,
          nodes: [node],
          count: Number(node.properties?.entity_count) || 1,
          anchor: [focalX, focalY],
          secondaryAnchors: [],
          naturalLeft,
          clearance,
          color,
          status: subtitle
        };
      });
    } else {
      // For dense detections (more than 8 nodes), cluster by anatomical organ
      const organBuckets = {};
      groundedNodes.forEach((node, idx) => {
        const labelLower = (node.label || '').toLowerCase();
        const catLower = (node.category || '').toLowerCase();
        const organProp = (node.properties?.organ || '').toLowerCase();

        let groupKey = 'general';
        let defaultTitle = node.label || 'Anatomical Feature';
        let systemName = 'Shoot System';

        if (
          organProp.includes('flower') || organProp.includes('bloom') ||
          labelLower.includes('bloom') || labelLower.includes('rose') ||
          labelLower.includes('petal') || labelLower.includes('corolla')
        ) {
          groupKey = 'petals_blooms';
          defaultTitle = 'Petals & Blooms';
          systemName = 'Shoot System';
        } else if (
          organProp.includes('leaf') || labelLower.includes('leaf') ||
          labelLower.includes('leaves') || labelLower.includes('foliage') ||
          labelLower.includes('chloros') || labelLower.includes('canopy')
        ) {
          groupKey = 'leaves_foliage';
          defaultTitle = 'Leaves & Foliage';
          systemName = 'Shoot System';
        } else if (
          organProp.includes('stem') || labelLower.includes('stem') ||
          labelLower.includes('shoot') || labelLower.includes('cutting') ||
          labelLower.includes('stalk') || labelLower.includes('branch')
        ) {
          groupKey = 'stems_shoots';
          defaultTitle = 'Stems & Shoots';
          systemName = 'Shoot System';
        } else if (
          organProp.includes('root') || labelLower.includes('root') ||
          labelLower.includes('rhizome') || labelLower.includes('callus') ||
          labelLower.includes('substrate') || labelLower.includes('soil')
        ) {
          groupKey = 'root_system';
          defaultTitle = 'Root System';
          systemName = 'Root System';
        } else if (
          organProp.includes('fruit') || labelLower.includes('fruit') ||
          labelLower.includes('berry') || labelLower.includes('tomato')
        ) {
          groupKey = 'fruit_cluster';
          defaultTitle = 'Fruit Clusters';
          systemName = 'Shoot System';
        } else if (
          labelLower.includes('sensor') || labelLower.includes('probe') ||
          catLower.includes('measurement')
        ) {
          groupKey = 'telemetry_sensor';
          defaultTitle = 'Environmental Sensor';
          systemName = 'Sensor Network';
        } else if (
          catLower.includes('pathology') || labelLower.includes('lesion') ||
          labelLower.includes('necros') || labelLower.includes('blight')
        ) {
          groupKey = 'pathology_site';
          defaultTitle = 'Pathology Site';
          systemName = 'Pathology Sites';
        } else {
          groupKey = `organ_${idx}`;
          defaultTitle = node.label;
        }

        if (!organBuckets[groupKey]) {
          const organColor = SEMANTIC_ORGAN_COLORS[groupKey] || ANCHOR_COLORS[Object.keys(organBuckets).length % ANCHOR_COLORS.length];
          organBuckets[groupKey] = {
            key: groupKey,
            title: defaultTitle,
            systemName,
            nodes: [],
            color: organColor
          };
        }
        organBuckets[groupKey].nodes.push(node);
      });

      Object.values(organBuckets).forEach((group) => {
        let primaryNode = group.nodes[0];
        let maxScore = -1;
        group.nodes.forEach((n) => {
          const w = Math.abs(n.bbox[3] - n.bbox[1]);
          const h = Math.abs(n.bbox[2] - n.bbox[0]);
          const area = w * h;
          const conf = Number(n.confidence) || 0.9;
          const isTooLarge = w > 480 || h > 480;
          const isTiny = w < 30 || h < 30;
          let score = conf * 100;
          if (isTooLarge) score *= 0.05;
          else if (isTiny) score *= 0.2;
          else score *= Math.min(Math.sqrt(area) / 180, 1.4);
          if (score > maxScore) {
            maxScore = score;
            primaryNode = n;
          }
        });

        let focalY = Math.round((primaryNode.bbox[0] + primaryNode.bbox[2]) / 2);
        let focalX = Math.round((primaryNode.bbox[1] + primaryNode.bbox[3]) / 2);
        if (Array.isArray(primaryNode.properties?.focal_point) && primaryNode.properties.focal_point.length === 2) {
          focalX = primaryNode.properties.focal_point[0];
          focalY = primaryNode.properties.focal_point[1];
        }

        const naturalLeft = focalX < 500;
        const clearance = naturalLeft ? focalX : 1000 - focalX;

        candidates.push({
          id: group.key,
          key: group.key,
          title: group.title,
          subtitle: primaryNode.properties?.condition || primaryNode.category || 'morphology',
          systemName: group.systemName,
          primaryNode,
          node: primaryNode,
          nodes: group.nodes,
          count: group.nodes.length,
          anchor: [focalX, focalY],
          secondaryAnchors: group.nodes.filter(n => n.id !== primaryNode.id).map(n => [
            Math.round((n.bbox[1] + n.bbox[3]) / 2),
            Math.round((n.bbox[0] + n.bbox[2]) / 2)
          ]),
          naturalLeft,
          clearance,
          color: group.color,
          status: primaryNode.properties?.condition || primaryNode.category || 'morphology'
        });
      });
    }

    // Distribute callouts across left and right margins to balance layout and prevent clutter
    const leftCallouts = [];
    const rightCallouts = [];

    // Sort candidates vertically from top to bottom
    candidates.sort((a, b) => a.anchor[1] - b.anchor[1]);

    if (candidates.length <= 4) {
      // Natural side distribution for small sets
      candidates.forEach((c) => {
        if (c.naturalLeft) leftCallouts.push(c);
        else rightCallouts.push(c);
      });
      // If all ended up on one side, move the one with deepest center to the opposite side
      if (leftCallouts.length === 0 && rightCallouts.length > 1) {
        leftCallouts.push(rightCallouts.shift());
      } else if (rightCallouts.length === 0 && leftCallouts.length > 1) {
        rightCallouts.push(leftCallouts.pop());
      }
    } else {
      // Balanced distribution: alternate based on natural side with a max of 4 per side
      candidates.forEach((c) => {
        if (c.naturalLeft && leftCallouts.length < 4) {
          leftCallouts.push(c);
        } else if (!c.naturalLeft && rightCallouts.length < 4) {
          rightCallouts.push(c);
        } else if (leftCallouts.length < 4) {
          leftCallouts.push(c);
        } else if (rightCallouts.length < 4) {
          rightCallouts.push(c);
        }
      });
    }

    // Leader line geometry routing to OUTSIDE margins (like a botanical textbook diagram):
    // Left margin target: x = 0 (exact left border of specimen image)
    // Right margin target: x = 1000 (exact right border of specimen image)
    const layoutSide = (items, isLeft) => {
      if (items.length === 0) return [];
      items.sort((a, b) => a.anchor[1] - b.anchor[1]);

      const minGap = Math.max(12, Math.floor(76 / Math.max(1, items.length)));

      let centers = items.map((it) => Math.max(10, Math.min(90, it.anchor[1] / 10)));

      // Push overlapping labels down
      for (let i = 1; i < centers.length; i++) {
        if (centers[i] - centers[i - 1] < minGap) {
          centers[i] = centers[i - 1] + minGap;
        }
      }
      // If bottom-most label exceeds safe boundary, push back up
      if (centers[centers.length - 1] > 90) {
        centers[centers.length - 1] = 90;
        for (let i = centers.length - 2; i >= 0; i--) {
          if (centers[i + 1] - centers[i] < minGap) {
            centers[i] = Math.max(10, centers[i + 1] - minGap);
          }
        }
      }

      return items.map((item, i) => {
        const cardCenterY_pct = centers[i];
        const cardCenterY_1000 = Math.round(cardCenterY_pct * 10);

        // Leader line exits the image frame at the border into the margin connector:
        const targetX_1000 = isLeft ? 0 : 1000;
        const targetY_1000 = cardCenterY_1000;

        // Clean dogleg horizontal elbow geometry:
        // Transition to horizontal line before reaching the image boundary
        const anchorX = item.anchor[0];
        let elbowX_1000;
        if (isLeft) {
          elbowX_1000 = Math.min(anchorX - 25, Math.max(40, anchorX * 0.45));
        } else {
          elbowX_1000 = Math.max(anchorX + 25, Math.min(960, anchorX + (1000 - anchorX) * 0.55));
        }
        const elbowY_1000 = targetY_1000;

        return {
          ...item,
          isLeft,
          id: `callout_${item.key || item.id}`,
          cardCenterY_pct,
          lineTarget: [targetX_1000, targetY_1000],
          elbowPoint: [elbowX_1000, elbowY_1000]
        };
      });
    };

    const positionedLeft = layoutSide(leftCallouts, true);
    const positionedRight = layoutSide(rightCallouts, false);

    return [...positionedLeft, ...positionedRight];
  }, [groundedNodes]);

  // Derive vertical system grouping brackets for left margin callouts (matching Image 2's Shoot system / Root system brackets)
  const leftSystemBrackets = useMemo(() => {
    const leftItems = anatomicalCallouts.filter((c) => c.isLeft);
    if (leftItems.length < 2) return [];

    const groups = {};
    leftItems.forEach((it) => {
      const sys = it.systemName || 'Shoot System';
      if (!groups[sys]) groups[sys] = [];
      groups[sys].push(it);
    });

    const brackets = [];
    Object.entries(groups).forEach(([sysName, items]) => {
      if (items.length >= 2) {
        const topPct = Math.min(...items.map((it) => it.cardCenterY_pct));
        const bottomPct = Math.max(...items.map((it) => it.cardCenterY_pct));
        brackets.push({
          systemName: sysName,
          topPct: Math.max(5, topPct - 3),
          bottomPct: Math.min(95, bottomPct + 3),
          color: items[0].color?.stroke || 'var(--primary)'
        });
      }
    });
    return brackets;
  }, [anatomicalCallouts]);

  const effectiveDomain = String(domain || preset?.domain || (presetId && presetId.startsWith('agri') ? 'agriculture' : (presetId && presetId.startsWith('pediat') ? 'pediatrics' : '')) || '').toLowerCase();

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

  // Handle right-click on image canvas or entity to trigger "Ask SAAR" & friendly tool suggestions
  const handleCanvasContextMenu = (e, node = null) => {
    e.preventDefault();
    e.stopPropagation();

    let targetNode = node;
    if (!targetNode && imageContainerRef.current && groundedNodes && groundedNodes.length > 0) {
      const rect = imageContainerRef.current.getBoundingClientRect();
      const rawX = e.clientX - rect.left;
      const rawY = e.clientY - rect.top;
      const scaleX = 1000 / Math.max(1, rect.width);
      const scaleY = 1000 / Math.max(1, rect.height);
      const svgX = rawX * scaleX;
      const svgY = rawY * scaleY;
      targetNode = groundedNodes.find((n) => {
        if (!n.bbox || n.bbox.length !== 4) return false;
        const [ymin, xmin, ymax, xmax] = n.bbox;
        return svgX >= xmin && svgX <= xmax && svgY >= ymin && svgY <= ymax;
      }) || null;
    }

    const x = Math.min(Math.max(10, e.clientX), (typeof window !== 'undefined' ? window.innerWidth : 1000) - 270);
    const y = Math.min(Math.max(10, e.clientY), (typeof window !== 'undefined' ? window.innerHeight : 800) - 180);

    setContextMenu({ x, y, node: targetNode });
  };

  // Close context menu on outside click or window scroll
  useEffect(() => {
    const handleCloseMenu = (e) => {
      if (contextMenu && !e.target.closest('.image-canvas-context-menu')) {
        setContextMenu(null);
      }
    };
    window.addEventListener('click', handleCloseMenu);
    window.addEventListener('scroll', handleCloseMenu, true);
    return () => {
      window.removeEventListener('click', handleCloseMenu);
      window.removeEventListener('scroll', handleCloseMenu, true);
    };
  }, [contextMenu]);

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

          {/* Annotation Mode Switcher: Callout Diagram vs Bounding Boxes */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            background: 'var(--bg-dark)',
            borderRadius: '6px',
            padding: '2px',
            border: '1px solid var(--border-color)'
          }}>
            <button
              type="button"
              onClick={() => setAnnotationMode('callouts')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                padding: '0.22rem 0.5rem',
                borderRadius: '4px',
                border: 'none',
                background: annotationMode === 'callouts' ? 'rgba(56, 189, 248, 0.18)' : 'transparent',
                color: annotationMode === 'callouts' ? 'var(--primary)' : 'var(--text-muted)',
                fontWeight: annotationMode === 'callouts' ? 700 : 500,
                fontSize: '0.68rem',
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
              title="Botanical diagram with leader lines & consolidated counts (like textbook diagrams)"
            >
              <Sparkles size={11} />
              <span>Callout Diagram</span>
            </button>
            <button
              type="button"
              onClick={() => setAnnotationMode('boxes')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                padding: '0.22rem 0.5rem',
                borderRadius: '4px',
                border: 'none',
                background: annotationMode === 'boxes' ? 'rgba(56, 189, 248, 0.18)' : 'transparent',
                color: annotationMode === 'boxes' ? 'var(--primary)' : 'var(--text-muted)',
                fontWeight: annotationMode === 'boxes' ? 700 : 500,
                fontSize: '0.68rem',
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
              title="Traditional bounding box overlays"
            >
              <Crosshair size={11} />
              <span>Boxes</span>
            </button>
          </div>

          {/* Bounding Box Master Toggle (visible in boxes mode) */}
          {annotationMode === 'boxes' && (
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
          )}

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
      <div
        ref={imageContainerRef}
        onContextMenu={(e) => handleCanvasContextMenu(e, null)}
        style={{
          position: 'relative',
          width: '100%',
          minHeight: '260px',
          borderRadius: '10px',
          border: '1px solid var(--border-color)',
          background: 'var(--bg-card)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: annotationMode === 'callouts' ? '24px 260px' : '10px',
          boxShadow: '0 2px 10px var(--border-glow)',
          overflow: 'visible',
          boxSizing: 'border-box'
        }}>
        {/* Media Rendering: Video or Image */}
        {displayImage || customVideoUrl ? (
          <div
            style={{
              position: 'relative',
              display: 'inline-block',
              maxWidth: '100%',
              lineHeight: 0,
              borderRadius: '8px',
              overflow: 'visible',
              boxShadow: '0 4px 16px rgba(0, 0, 0, 0.12)'
            }}
          >
            {mediaMode === 'video' ? (
              customVideoUrl ? (
                <video
                  ref={videoRef}
                  src={customVideoUrl}
                  onTimeUpdate={handleVideoTimeUpdate}
                  playsInline
                  style={{
                    maxWidth: '100%',
                    maxHeight: '480px',
                    width: 'auto',
                    height: 'auto',
                    display: 'block',
                    borderRadius: '8px'
                  }}
                />
              ) : (
                <div style={{ position: 'relative', maxWidth: '100%', lineHeight: 0 }}>
                  <img
                    src={displayImage}
                    alt="Temporal Video Keyframe"
                    style={{
                      maxWidth: '100%',
                      maxHeight: '480px',
                      width: 'auto',
                      height: 'auto',
                      display: 'block',
                      borderRadius: '8px',
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
                    <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: isVideoPlaying ? '#38bdf8' : 'var(--text-muted)' }} />
                    <span>{isVideoPlaying ? 'PLAYING' : 'PAUSED'}</span>
                    <span>•</span>
                    <span>{videoCurrentTime.toFixed(1)}s / {videoDuration.toFixed(1)}s</span>
                  </div>
                </div>
              )
            ) : (
              <img
                src={displayImage}
                alt="Visual Evidence"
                onError={(e) => {
                  if (!e.target.src.includes('monstera_sample.png')) {
                    e.target.src = '/monstera_sample.png';
                  }
                }}
                style={{
                  maxWidth: '100%',
                  maxHeight: '480px',
                  width: 'auto',
                  height: 'auto',
                  display: 'block',
                  borderRadius: '8px'
                }}
              />
            )}

            {/* SVG Annotations Overlay: strictly mapped to 100% of the image pixels */}
            {groundedNodes.length > 0 && (
              <svg
                viewBox="0 0 1000 1000"
                preserveAspectRatio="none"
                style={{
                  position: 'absolute',
                  inset: 0,
                  width: '100%',
                  height: '100%',
                  overflow: 'visible',
                  pointerEvents: 'none',
                  zIndex: 5
                }}
              >
                <defs>
                  <filter id="box-glow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="5" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                  </filter>
                  <filter id="leader-shadow" x="-30%" y="-30%" width="160%" height="160%">
                    <feDropShadow dx="0" dy="1" stdDeviation="1.2" floodColor="rgba(0, 0, 0, 0.55)" />
                  </filter>
                </defs>

                {annotationMode === 'callouts' ? (
                  // 1. Anatomical Leader Lines & Precision Reticles
                  anatomicalCallouts.map((callout) => {
                    const isSelected = selectedNodeId && callout.nodes.some((n) => n.id === selectedNodeId);
                    const isHovered = hoveredBoxId === callout.id;
                    const strokeColor = isSelected ? 'var(--text-main)' : isHovered ? 'var(--primary)' : callout.color.stroke;
                    const [anchorX, anchorY] = callout.anchor;
                    const [elbowX, elbowY] = callout.elbowPoint;
                    const [targetX, targetY] = callout.lineTarget;
                    const linePath = `M ${anchorX} ${anchorY} L ${elbowX} ${elbowY} L ${targetX} ${targetY}`;

                    return (
                      <g key={callout.id}>
                        {/* Secondary instance markers on other detected members of this organ */}
                        {callout.secondaryAnchors && callout.secondaryAnchors.map(([secX, secY], sIdx) => (
                          <g key={`sec_${callout.id}_${sIdx}`}>
                            <circle
                              cx={secX}
                              cy={secY}
                              r="6"
                              fill="transparent"
                              stroke={callout.color.stroke}
                              strokeWidth="1.3"
                              strokeDasharray="2 2"
                              opacity={isSelected || isHovered ? 0.95 : 0.7}
                              filter="url(#leader-shadow)"
                            />
                            <circle cx={secX} cy={secY} r="2" fill={callout.color.stroke} opacity={0.8} />
                          </g>
                        ))}

                        {/* High-contrast background outline for universal visibility over any image background */}
                        <path
                          d={linePath}
                          fill="none"
                          stroke="var(--bg-dark)"
                          strokeWidth={isSelected ? 4.8 : isHovered ? 4.2 : 3.6}
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          opacity="0.95"
                        />
                        {/* Leader line with textbook dogleg horizontal landing */}
                        <path
                          d={linePath}
                          fill="none"
                          stroke={strokeColor}
                          strokeWidth={isSelected ? 2.6 : isHovered ? 2.2 : 1.8}
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />

                        {/* Terminal pin at card connector edge */}
                        <circle cx={targetX} cy={targetY} r="4.5" fill="var(--bg-dark)" />
                        <circle cx={targetX} cy={targetY} r="3" fill={strokeColor} />

                        {/* Primary focal anchor precision reticle */}
                        <circle
                          cx={anchorX}
                          cy={anchorY}
                          r={isSelected ? 11 : isHovered ? 9.5 : 8}
                          fill={callout.color.fill}
                          stroke="var(--bg-dark)"
                          strokeWidth={isSelected ? 4.2 : 3.4}
                        />
                        <circle
                          cx={anchorX}
                          cy={anchorY}
                          r={isSelected ? 11 : isHovered ? 9.5 : 8}
                          fill="none"
                          stroke={strokeColor}
                          strokeWidth={isSelected ? 2.4 : 1.8}
                        />
                        {/* Solid center focal point */}
                        <circle cx={anchorX} cy={anchorY} r="4" fill="var(--bg-dark)" />
                        <circle cx={anchorX} cy={anchorY} r="2.8" fill={strokeColor} />

                        {/* Precision crosshair tick marks (N, S, E, W) */}
                        <line x1={anchorX - 8} y1={anchorY} x2={anchorX - 4} y2={anchorY} stroke={strokeColor} strokeWidth="1.6" strokeLinecap="round" />
                        <line x1={anchorX + 4} y1={anchorY} x2={anchorX + 8} y2={anchorY} stroke={strokeColor} strokeWidth="1.6" strokeLinecap="round" />
                        <line x1={anchorX} y1={anchorY - 8} x2={anchorX} y2={anchorY - 4} stroke={strokeColor} strokeWidth="1.6" strokeLinecap="round" />
                        <line x1={anchorX} y1={anchorY + 4} x2={anchorX} y2={anchorY + 8} stroke={strokeColor} strokeWidth="1.6" strokeLinecap="round" />
                      </g>
                    );
                  })
                ) : (
                  // 2. Traditional Bounding Box Overlay
                  groundedNodes.map((node, idx) => {
                    if (!visibleBoxIds.has(node.id)) return null;

                    const color = ANCHOR_COLORS[idx % ANCHOR_COLORS.length];
                    const [ymin, xmin, ymax, xmax] = node.bbox;
                    const width = Math.max(30, xmax - xmin);
                    const height = Math.max(30, ymax - ymin);
                    const isSelected = Boolean(
                      selectedNodeId &&
                        (node.id === selectedNodeId ||
                          node.id.toLowerCase() === selectedNodeId.toLowerCase() ||
                          node.label?.toLowerCase().includes(selectedNodeId.toLowerCase()))
                    );
                    const isHovered = hoveredBoxId === node.id;
                    const labelWidth = Math.min(Math.max(width, 130), 220);

                    return (
                      <g
                        key={node.id}
                        style={{ pointerEvents: 'auto', cursor: 'pointer', transition: 'all 0.15s ease-out' }}
                        onClick={(e) => {
                          e.stopPropagation();
                          if (onSelectNode) onSelectNode(isSelected ? null : node.id);
                        }}
                        onContextMenu={(e) => handleCanvasContextMenu(e, node)}
                        onMouseEnter={() => setHoveredBoxId(node.id)}
                        onMouseLeave={() => setHoveredBoxId(null)}
                      >
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
                        <g transform={`translate(${xmin}, ${Math.max(6, ymin - 26)})`}>
                          <rect
                            x="0"
                            y="0"
                            width={labelWidth}
                            height="24"
                            rx="5"
                            fill={isSelected ? color.stroke : isHovered ? 'rgba(15, 23, 42, 0.95)' : 'rgba(15, 23, 42, 0.88)'}
                          />
                          <text x="8" y="16" fill="#ffffff" fontSize="11" fontWeight="600">
                            {node.label}
                          </text>
                        </g>
                      </g>
                    );
                  })
                )}
              </svg>
            )}

            {/* 3. HTML Outside Callout Labels Overlay (Outside the specimen image, matching textbook diagram) */}
            {annotationMode === 'callouts' && (
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  pointerEvents: 'none',
                  zIndex: 10
                }}
              >
                {/* Anatomical System Brackets (inspired by Image 2's Shoot system / Root system brackets) */}
                {leftSystemBrackets && leftSystemBrackets.map((bracket) => (
                  <div
                    key={`bracket_${bracket.systemName}`}
                    style={{
                      position: 'absolute',
                      top: `${bracket.topPct}%`,
                      height: `${Math.max(12, bracket.bottomPct - bracket.topPct)}%`,
                      right: 'calc(100% + 228px)',
                      display: 'flex',
                      alignItems: 'center',
                      pointerEvents: 'none',
                      zIndex: 8
                    }}
                  >
                    <span
                      style={{
                        writingMode: 'vertical-rl',
                        transform: 'rotate(180deg)',
                        fontSize: '0.62rem',
                        fontWeight: 700,
                        letterSpacing: '0.06em',
                        textTransform: 'uppercase',
                        color: bracket.color,
                        marginRight: '6px',
                        opacity: 0.85
                      }}
                    >
                      {bracket.systemName}
                    </span>
                    <div
                      style={{
                        position: 'relative',
                        width: '7px',
                        height: '100%',
                        borderLeft: `1.8px solid ${bracket.color}`,
                        borderTop: `1.8px solid ${bracket.color}`,
                        borderBottom: `1.8px solid ${bracket.color}`,
                        borderRadius: '2px 0 0 2px',
                        opacity: 0.75
                      }}
                    />
                  </div>
                ))}

                {anatomicalCallouts.map((callout) => {
                  const isSelected = selectedNodeId && callout.nodes.some((n) => n.id === selectedNodeId);
                  const isHovered = hoveredBoxId === callout.id;
                  const accentColor = callout.color.stroke;

                  return (
                    <div
                      key={callout.id}
                      onClick={(e) => {
                        e.stopPropagation();
                        if (onSelectNode) onSelectNode(isSelected ? null : callout.primaryNode.id);
                      }}
                      onContextMenu={(e) => handleCanvasContextMenu(e, callout.primaryNode)}
                      onMouseEnter={() => setHoveredBoxId(callout.id)}
                      onMouseLeave={() => setHoveredBoxId(null)}
                      style={{
                        position: 'absolute',
                        top: `${callout.cardCenterY_pct}%`,
                        transform: 'translateY(-50%)',
                        right: callout.isLeft ? '100%' : 'auto',
                        left: callout.isLeft ? 'auto' : '100%',
                        display: 'flex',
                        alignItems: 'center',
                        flexDirection: 'row',
                        pointerEvents: 'auto',
                        cursor: 'pointer',
                        zIndex: isSelected || isHovered ? 25 : 12,
                        transition: 'all 0.16s ease'
                      }}
                    >
                      {/* Left Callout Layout: [Card] ---> [Leader Stem Line] ---> (touches image border) */}
                      {callout.isLeft ? (
                        <>
                          {/* The Textbook Callout Card */}
                          <div
                            style={{
                              width: '200px',
                              display: 'flex',
                              flexDirection: 'column',
                              alignItems: 'flex-end',
                              textAlign: 'right',
                              padding: '6px 12px',
                              borderRadius: '6px',
                              background: isSelected ? 'var(--primary-bg)' : isHovered ? 'var(--bg-card-hover)' : 'var(--bg-card)',
                              backdropFilter: 'blur(16px)',
                              WebkitBackdropFilter: 'blur(16px)',
                              color: 'var(--text-main)',
                              border: isSelected
                                ? `1.5px solid ${accentColor}`
                                : isHovered
                                ? `1px solid ${accentColor}`
                                : `1px solid var(--border-color)`,
                              borderRight: `3.5px solid ${accentColor}`,
                              boxShadow: isSelected
                                ? `0 0 0 2px ${callout.color.glow}, 0 4px 14px rgba(0,0,0,0.12)`
                                : isHovered
                                ? `0 4px 12px rgba(0,0,0,0.1)`
                                : '0 2px 8px rgba(0,0,0,0.06)',
                              userSelect: 'none',
                              boxSizing: 'border-box'
                            }}
                          >
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '6px', width: '100%' }}>
                              <span
                                style={{
                                  fontFamily: 'var(--font-heading)',
                                  fontWeight: 700,
                                  fontSize: '0.82rem',
                                  color: isSelected ? accentColor : 'var(--text-main)',
                                  lineHeight: 1.2
                                }}
                                title={callout.title}
                              >
                                {callout.title}
                              </span>
                              <span
                                style={{
                                  width: '6px',
                                  height: '6px',
                                  minWidth: '6px',
                                  borderRadius: '50%',
                                  background: accentColor,
                                  boxShadow: `0 0 5px ${accentColor}`
                                }}
                              />
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '6px', marginTop: '2px', width: '100%' }}>
                              <span
                                style={{
                                  fontSize: '0.62rem',
                                  color: 'var(--text-dim)',
                                  textTransform: 'uppercase',
                                  letterSpacing: '0.04em',
                                  fontWeight: 600,
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  whiteSpace: 'nowrap',
                                  maxWidth: '125px'
                                }}
                                title={callout.subtitle || callout.status}
                              >
                                {callout.subtitle || callout.status}
                              </span>
                              {callout.count > 1 && (
                                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.6rem', fontWeight: 800, padding: '0.5px 4px', borderRadius: '3px', background: 'var(--primary-bg)', color: 'var(--primary)', border: '1px solid var(--primary-glow)' }}>
                                  {callout.count}×
                                </span>
                              )}
                              <span style={{ fontSize: '0.62rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontWeight: 700, flexShrink: 0 }}>
                                {Math.round((callout.primaryNode?.confidence || 0.95) * 100)}%
                              </span>
                            </div>
                          </div>

                          {/* Seamless Horizontal Leader Stem Line touching image border */}
                          <div
                            style={{
                              width: '28px',
                              height: isSelected ? '2.4px' : isHovered ? '2px' : '1.8px',
                              background: accentColor,
                              boxShadow: `0 0 4px ${callout.color.glow}`,
                              flexShrink: 0
                            }}
                          />
                        </>
                      ) : (
                        <>
                          {/* Right Callout Layout: (touches image border) ---> [Leader Stem Line] ---> [Card] */}
                          <div
                            style={{
                              width: '28px',
                              height: isSelected ? '2.4px' : isHovered ? '2px' : '1.8px',
                              background: accentColor,
                              boxShadow: `0 0 4px ${callout.color.glow}`,
                              flexShrink: 0
                            }}
                          />

                          {/* The Textbook Callout Card */}
                          <div
                            style={{
                              width: '200px',
                              display: 'flex',
                              flexDirection: 'column',
                              alignItems: 'flex-start',
                              textAlign: 'left',
                              padding: '6px 12px',
                              borderRadius: '6px',
                              background: isSelected ? 'var(--primary-bg)' : isHovered ? 'var(--bg-card-hover)' : 'var(--bg-card)',
                              backdropFilter: 'blur(16px)',
                              WebkitBackdropFilter: 'blur(16px)',
                              color: 'var(--text-main)',
                              border: isSelected
                                ? `1.5px solid ${accentColor}`
                                : isHovered
                                ? `1px solid ${accentColor}`
                                : `1px solid var(--border-color)`,
                              borderLeft: `3.5px solid ${accentColor}`,
                              boxShadow: isSelected
                                ? `0 0 0 2px ${callout.color.glow}, 0 4px 14px rgba(0,0,0,0.12)`
                                : isHovered
                                ? `0 4px 12px rgba(0,0,0,0.1)`
                                : '0 2px 8px rgba(0,0,0,0.06)',
                              userSelect: 'none',
                              boxSizing: 'border-box'
                            }}
                          >
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-start', gap: '6px', width: '100%' }}>
                              <span
                                style={{
                                  width: '6px',
                                  height: '6px',
                                  minWidth: '6px',
                                  borderRadius: '50%',
                                  background: accentColor,
                                  boxShadow: `0 0 5px ${accentColor}`
                                }}
                              />
                              <span
                                style={{
                                  fontFamily: 'var(--font-heading)',
                                  fontWeight: 700,
                                  fontSize: '0.82rem',
                                  color: isSelected ? accentColor : 'var(--text-main)',
                                  lineHeight: 1.2
                                }}
                                title={callout.title}
                              >
                                {callout.title}
                              </span>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-start', gap: '6px', marginTop: '2px', width: '100%' }}>
                              <span
                                style={{
                                  fontSize: '0.62rem',
                                  color: 'var(--text-dim)',
                                  textTransform: 'uppercase',
                                  letterSpacing: '0.04em',
                                  fontWeight: 600,
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  whiteSpace: 'nowrap',
                                  maxWidth: '125px'
                                }}
                                title={callout.subtitle || callout.status}
                              >
                                {callout.subtitle || callout.status}
                              </span>
                              {callout.count > 1 && (
                                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.6rem', fontWeight: 800, padding: '0.5px 4px', borderRadius: '3px', background: 'var(--primary-bg)', color: 'var(--primary)', border: '1px solid var(--primary-glow)' }}>
                                  {callout.count}×
                                </span>
                              )}
                              <span style={{ fontSize: '0.62rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontWeight: 700, flexShrink: 0 }}>
                                {Math.round((callout.primaryNode?.confidence || 0.95) * 100)}%
                              </span>
                            </div>
                          </div>
                        </>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ) : (
          <div
            onClick={() => fileInputRef.current?.click()}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '2.5rem 1rem',
              cursor: 'pointer',
              width: '100%',
              height: '100%',
              minHeight: '260px',
              background: 'radial-gradient(ellipse at center, rgba(56, 189, 248, 0.05) 0%, rgba(9, 13, 22, 0.95) 75%)',
              border: '2px dashed rgba(56, 189, 248, 0.25)',
              borderRadius: '8px',
              boxSizing: 'border-box'
            }}
          >
            <div style={{
              width: '46px',
              height: '46px',
              borderRadius: '12px',
              background: 'rgba(56, 189, 248, 0.12)',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '0.75rem'
            }}>
              <Upload size={20} color="var(--primary)" />
            </div>
            <div style={{ fontWeight: 700, fontSize: '0.86rem', color: 'var(--text-main)', marginBottom: '0.25rem' }}>
              Upload Specimen Photo or Video
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textAlign: 'center', maxWidth: '280px' }}>
              Drop an image here, click to browse, or paste an image URL for anatomical grounding & causal reasoning
            </div>
          </div>
        )}

      </div>

      {/* Theme-Aware Full-Width Bottom Bar with Right-Click Hint */}
      {displayImage && (
        <div style={{
          width: '100%',
          marginTop: '10px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
          boxShadow: '0 1px 4px var(--border-glow)',
          padding: '0.4rem 0.9rem',
          borderRadius: '7px',
          color: 'var(--text-main)',
          fontSize: '0.7rem',
          boxSizing: 'border-box'
        }}>
          <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>
            {mediaMode === 'video' ? `Keyframe @ ${videoCurrentTime.toFixed(1)}s: ${activeKeyframe?.label || 'Continuous Track'}` : preset?.title || "Visual Evidence Grounding"}
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <span style={{ fontSize: '0.66rem', color: 'var(--primary)', fontWeight: 600 }}>
              💡 Click any label to trace leader line on specimen
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: visibleBoxIds.size > 0 ? 'var(--primary)' : 'var(--text-muted)' }}>
              {visibleBoxIds.size} of {groundedNodes.length} Active
            </span>
          </div>
        </div>
      )}

        {/* Right-Click Context Menu: Ask SAAR & Field Suggestions */}
        {contextMenu && (
          <div
            className="image-canvas-context-menu animate-fade-in"
            style={{
              position: 'fixed',
              top: `${contextMenu.y}px`,
              left: `${contextMenu.x}px`,
              zIndex: 9999,
              minWidth: '220px',
              maxWidth: '280px',
              background: 'rgba(15, 23, 42, 0.97)',
              backdropFilter: 'blur(12px)',
              border: '1px solid rgba(56, 189, 248, 0.45)',
              borderRadius: '8px',
              boxShadow: '0 8px 30px rgba(0, 0, 0, 0.6), 0 0 16px rgba(56, 189, 248, 0.25)',
              padding: '6px',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px',
              pointerEvents: 'auto'
            }}
            onClick={(e) => e.stopPropagation()}
            onContextMenu={(e) => e.preventDefault()}
          >
            {/* Header / Target indicator */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '3px 6px 5px',
              borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
              fontSize: '0.67rem',
              color: 'var(--text-muted)'
            }}>
              <span style={{ fontWeight: 700, color: '#38bdf8', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '180px' }}>
                {contextMenu.node ? contextMenu.node.label : 'Visual Region'}
              </span>
              <button
                type="button"
                onClick={() => setContextMenu(null)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '1px' }}
              >
                <X size={12} />
              </button>
            </div>

            {/* 1. Primary: Ask SAAR */}
            <button
              type="button"
              className="context-menu-item"
              onClick={() => {
                const prompt = contextMenu.node
                  ? `Can you explain the causal findings, physical characteristics, and diagnostic relevance of "${contextMenu.node.label}"?`
                  : `Can you analyze the visual evidence and physical mechanisms visible in this region?`;
                if (onAskQuery) onAskQuery(prompt);
                setContextMenu(null);
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '7px 9px',
                borderRadius: '5px',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                background: 'rgba(56, 189, 248, 0.12)',
                color: '#ffffff',
                fontSize: '0.74rem',
                fontWeight: 600,
                cursor: 'pointer',
                textAlign: 'left',
                width: '100%'
              }}
            >
              <Sparkles size={14} color="#38bdf8" />
              <span>Ask SAAR about this {contextMenu.node ? 'entity' : 'area'}</span>
            </button>

            {/* 2. Suggested Field Analysis (if entity selected) */}
            {contextMenu.node && (() => {
              const mapping = getToolMapping(contextMenu.node.id);
              return (
                <div style={{ marginTop: '2px', paddingTop: '4px', borderTop: '1px solid rgba(255, 255, 255, 0.05)' }}>
                  <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', padding: '2px 6px', marginBottom: '2px' }}>
                    {mapping.userSuggestion}
                  </div>
                  <button
                    type="button"
                    className="context-menu-item"
                    onClick={() => {
                      if (onOpenTool) onOpenTool(mapping.toolId, contextMenu.node);
                      setContextMenu(null);
                    }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      width: '100%',
                      padding: '6px 8px',
                      borderRadius: '5px',
                      border: 'none',
                      background: 'rgba(255, 255, 255, 0.05)',
                      color: 'var(--primary)',
                      fontSize: '0.72rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      textAlign: 'left'
                    }}
                  >
                    <span>{mapping.actionText}</span>
                    <ArrowRight size={12} />
                  </button>
                </div>
              );
            })()}
          </div>
        )}

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



      {/* 4. Detected Visual Objects Directory (Consolidated Anatomical Systems vs Granular Boxes) */}
      {groundedNodes.length > 0 ? (
        annotationMode === 'callouts' ? (
          <div style={{ marginTop: '0.85rem' }}>
            {/* Section Header: Anatomical Organ Systems */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '0.55rem',
              flexWrap: 'wrap',
              gap: '0.5rem',
              padding: '0 0.1rem'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sparkles size={15} color="var(--primary)" />
                <span style={{ fontWeight: 700, fontSize: '0.84rem', color: 'var(--text-main)', letterSpacing: '0.2px' }}>
                  Anatomical Systems Directory
                </span>
                <span style={{
                  fontSize: '0.68rem',
                  fontFamily: 'var(--font-mono)',
                  padding: '0.12rem 0.45rem',
                  borderRadius: '10px',
                  background: 'var(--primary-bg)',
                  color: 'var(--primary)',
                  fontWeight: 700,
                  border: '1px solid var(--border-color)'
                }}>
                  {anatomicalCallouts.length} Organ Systems · {groundedNodes.length} Anchors Grounded
                </span>
              </div>
            </div>

            <div style={{ fontSize: '0.71rem', color: 'var(--text-muted)', marginBottom: '0.65rem' }}>
              Consolidated anatomical diagram view. Click any organ system to highlight its leader line on the specimen or explore in chat.
            </div>

            {/* Consolidated Organ System Cards (Only 3-4 clean cards total, never 20+ repetitive items!) */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(min(100%, 340px), 1fr))',
              gap: '0.55rem',
              paddingBottom: '2rem'
            }}>
              {anatomicalCallouts.map((callout) => {
                const isSelected = selectedNodeId && callout.nodes.some((n) => n.id === selectedNodeId);
                const isHovered = hoveredBoxId === callout.id;
                const toolMapping = getToolMapping(callout.primaryNode?.id);

                return (
                  <div
                    key={callout.id}
                    onClick={() => {
                      if (onSelectNode) onSelectNode(isSelected ? null : callout.primaryNode.id);
                    }}
                    onMouseEnter={() => setHoveredBoxId(callout.id)}
                    onMouseLeave={() => setHoveredBoxId(null)}
                    onContextMenu={(e) => handleCanvasContextMenu(e, callout.primaryNode)}
                    style={{
                      borderRadius: '8px',
                      border: isSelected
                        ? '1.5px solid var(--primary)'
                        : isHovered
                        ? '1px solid var(--primary)'
                        : '1px solid var(--border-color)',
                      background: isSelected ? 'var(--bg-card-hover)' : 'var(--bg-card)',
                      boxShadow: isSelected
                        ? '0 0 0 1px var(--primary), 0 2px 8px rgba(0,0,0,0.06)'
                        : '0 1px 2px rgba(0,0,0,0.03)',
                      padding: '0.65rem 0.8rem',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.45rem',
                      position: 'relative',
                      overflow: 'hidden'
                    }}
                  >
                    {/* Left accent bar */}
                    <div style={{
                      position: 'absolute',
                      left: 0,
                      top: 0,
                      bottom: 0,
                      width: '3.5px',
                      background: callout.color.stroke
                    }} />

                    {/* Header: Title + Plural Quantity Badge + Confidence */}
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', minWidth: 0 }}>
                        <div style={{
                          width: '8px',
                          height: '8px',
                          minWidth: '8px',
                          borderRadius: '50%',
                          background: callout.color.stroke,
                          boxShadow: `0 0 6px ${callout.color.stroke}`
                        }} />
                        <span style={{ fontWeight: 700, fontSize: '0.84rem', color: 'var(--text-main)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {callout.title}
                        </span>
                        {callout.count > 1 && (
                          <span style={{
                            background: 'rgba(56, 189, 248, 0.18)',
                            color: 'var(--primary)',
                            border: '1px solid rgba(56, 189, 248, 0.4)',
                            fontSize: '0.64rem',
                            fontWeight: 800,
                            padding: '0.08rem 0.4rem',
                            borderRadius: '4px'
                          }}>
                            {callout.count}× Items
                          </span>
                        )}
                      </div>

                      <span style={{
                        fontSize: '0.62rem',
                        fontFamily: 'var(--font-mono)',
                        fontWeight: 700,
                        padding: '0.12rem 0.42rem',
                        borderRadius: '4px',
                        background: 'rgba(5, 150, 105, 0.1)',
                        color: '#059669'
                      }}>
                        {Math.round((callout.primaryNode?.confidence || 0.95) * 100)}%
                      </span>
                    </div>

                    {/* Properties summary row */}
                    <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '4px', paddingLeft: '4px' }}>
                      <span style={{
                        fontSize: '0.62rem',
                        textTransform: 'uppercase',
                        fontWeight: 700,
                        padding: '0.08rem 0.35rem',
                        borderRadius: '4px',
                        background: 'var(--primary-bg)',
                        color: 'var(--primary)'
                      }}>
                        {callout.key.replace(/_/g, ' ')}
                      </span>
                      <span style={{
                        fontSize: '0.62rem',
                        padding: '0.08rem 0.38rem',
                        borderRadius: '4px',
                        background: 'var(--bg-dark)',
                        border: '1px solid var(--border-color)',
                        color: 'var(--text-muted)'
                      }}>
                        Status: <strong style={{ color: 'var(--text-main)' }}>{callout.status}</strong>
                      </span>
                      <span style={{
                        fontSize: '0.62rem',
                        padding: '0.08rem 0.38rem',
                        borderRadius: '4px',
                        background: 'var(--bg-dark)',
                        border: '1px solid var(--border-color)',
                        color: 'var(--text-muted)'
                      }}>
                        {callout.nodes.length} Grounded Points
                      </span>
                    </div>

                    {/* Action Footer: Ask SAAR & Diagnostic Tool shortcut */}
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      marginTop: '2px',
                      paddingTop: '0.35rem',
                      borderTop: '1px solid var(--border-color)',
                      paddingLeft: '4px'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span style={{ fontSize: '0.66rem', color: 'var(--text-muted)' }}>
                          Click callout to highlight on canvas
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (onAskQuery) {
                            onAskQuery(`Analyze the anatomical condition, turgor, and causal factors affecting ${callout.title}.`);
                          }
                        }}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                          padding: '0.2rem 0.45rem',
                          borderRadius: '5px',
                          background: 'var(--primary-bg)',
                          border: '1px solid var(--primary)',
                          color: 'var(--primary)',
                          fontSize: '0.65rem',
                          fontWeight: 600,
                          cursor: 'pointer'
                        }}
                      >
                        <MessageSquare size={10} />
                        <span>Ask SAAR</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <div style={{ marginTop: '0.85rem' }}>
            {/* Section Header with Bulk Actions & Guidance */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '0.55rem',
              flexWrap: 'wrap',
              gap: '0.5rem',
              padding: '0 0.1rem'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Target size={15} color="var(--primary)" />
                <span style={{ fontWeight: 700, fontSize: '0.84rem', color: 'var(--text-main)', letterSpacing: '0.2px' }}>
                  Detected Objects
                </span>
                <span style={{
                  fontSize: '0.68rem',
                  fontFamily: 'var(--font-mono)',
                  padding: '0.12rem 0.45rem',
                  borderRadius: '10px',
                  background: visibleBoxIds.size > 0 ? 'var(--primary-bg)' : 'var(--bg-dark)',
                  color: visibleBoxIds.size > 0 ? 'var(--primary)' : 'var(--text-muted)',
                  fontWeight: 700,
                  border: '1px solid var(--border-color)'
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
                    background: visibleBoxIds.size === groundedNodes.length ? 'var(--primary-bg)' : 'var(--bg-card)',
                    border: visibleBoxIds.size === groundedNodes.length ? '1px solid var(--primary)' : '1px solid var(--border-color)',
                    color: visibleBoxIds.size === groundedNodes.length ? 'var(--primary)' : 'var(--text-main)',
                    fontSize: '0.7rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
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
                    background: visibleBoxIds.size === 0 ? 'var(--primary-bg)' : 'var(--bg-card)',
                    border: visibleBoxIds.size === 0 ? '1px solid var(--primary)' : '1px solid var(--border-color)',
                    color: visibleBoxIds.size === 0 ? 'var(--primary)' : 'var(--text-muted)',
                    fontSize: '0.7rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                  title="Hide all bounding boxes for an unobstructed view"
                >
                  <EyeOff size={12} />
                  <span>Hide All</span>
                </button>
              </div>
            </div>

            <div style={{ fontSize: '0.71rem', color: 'var(--text-muted)', marginBottom: '0.65rem' }}>
              Click any object to focus its bounding box. Right-click canvas or use Ask SAAR to explore details in chat.
            </div>

            {/* Cards List / Grid (Responsive 1-column in split pane, multi-column in wide mode) */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(min(100%, 340px), 1fr))',
              gap: '0.55rem',
              paddingBottom: '2rem'
            }}>
            {groundedNodes.map((node, idx) => {
              const color = ANCHOR_COLORS[idx % ANCHOR_COLORS.length];
              const isVisible = visibleBoxIds.has(node.id);
              const isHovered = hoveredBoxId === node.id;
              const isSelected = Boolean(
                selectedNodeId && (
                  node.id === selectedNodeId ||
                  node.id.toLowerCase() === selectedNodeId.toLowerCase() ||
                  node.label?.toLowerCase().includes(selectedNodeId.toLowerCase())
                )
              );

              return (
                <div
                  key={node.id}
                  onClick={() => {
                    if (onSelectNode) {
                      onSelectNode(isSelected ? null : node.id);
                    }
                    if (!isVisible) {
                      toggleBoxVisibility(node.id);
                    }
                  }}
                  onMouseEnter={() => setHoveredBoxId(node.id)}
                  onMouseLeave={() => setHoveredBoxId(null)}
                  onContextMenu={(e) => handleCanvasContextMenu(e, node)}
                  style={{
                    borderRadius: '8px',
                    border: isSelected
                      ? '1.5px solid var(--primary)'
                      : isHovered
                      ? '1px solid var(--primary)'
                      : '1px solid var(--border-color)',
                    background: isSelected
                      ? 'var(--bg-card-hover)'
                      : 'var(--bg-card)',
                    boxShadow: isSelected
                      ? '0 0 0 1px var(--primary), 0 2px 8px rgba(0,0,0,0.06)'
                      : isHovered
                      ? '0 2px 8px rgba(0,0,0,0.06)'
                      : '0 1px 2px rgba(0,0,0,0.03)',
                    padding: '0.65rem 0.8rem',
                    cursor: 'pointer',
                    transition: 'all 0.15s cubic-bezier(0.4, 0, 0.2, 1)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.45rem',
                    position: 'relative',
                    overflow: 'hidden'
                  }}
                >
                  {/* Left accent indicator bar */}
                  <div style={{
                    position: 'absolute',
                    left: 0,
                    top: 0,
                    bottom: 0,
                    width: '3.5px',
                    background: isVisible ? color.stroke : 'var(--border-color)',
                    opacity: isVisible || isSelected ? 1 : 0.4
                  }} />

                  {/* Card Header: Indicator dot, Object Label, Category, Confidence, and Toggle Pill */}
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px', paddingLeft: '4px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0, flex: 1 }}>
                      <span
                        style={{
                          width: '8px',
                          height: '8px',
                          minWidth: '8px',
                          borderRadius: '50%',
                          background: color.stroke,
                          opacity: isVisible ? 1 : 0.4,
                          boxShadow: isVisible ? `0 0 6px ${color.stroke}` : 'none',
                          transition: 'all 0.15s ease'
                        }}
                      />
                      <span
                        style={{
                          fontWeight: 700,
                          fontSize: '0.82rem',
                          color: 'var(--text-main)',
                          lineHeight: 1.3,
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis'
                        }}
                        title={node.label}
                      >
                        {node.label}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0 }}>
                      {/* Category Badge */}
                      <span style={{
                        textTransform: 'uppercase',
                        fontWeight: 700,
                        fontSize: '0.6rem',
                        padding: '0.12rem 0.42rem',
                        borderRadius: '4px',
                        background: 'var(--primary-bg)',
                        color: 'var(--primary)',
                        letterSpacing: '0.3px'
                      }}>
                        {node.category || 'entity'}
                      </span>

                      {/* Confidence Score */}
                      <span style={{
                        fontSize: '0.62rem',
                        fontFamily: 'var(--font-mono)',
                        fontWeight: 700,
                        padding: '0.12rem 0.42rem',
                        borderRadius: '4px',
                        background: 'rgba(5, 150, 105, 0.1)',
                        color: '#059669'
                      }}>
                        {Math.round((node.confidence || 0.9) * 100)}%
                      </span>

                      {/* Toggle State Button */}
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleBoxVisibility(node.id);
                        }}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '3px',
                          padding: '0.15rem 0.42rem',
                          borderRadius: '5px',
                          fontSize: '0.63rem',
                          fontWeight: 700,
                          background: isVisible ? 'var(--primary-bg)' : 'var(--bg-dark)',
                          border: isVisible ? '1px solid var(--primary)' : '1px solid var(--border-color)',
                          color: isVisible ? 'var(--primary)' : 'var(--text-muted)',
                          cursor: 'pointer',
                          flexShrink: 0,
                          transition: 'all 0.12s ease'
                        }}
                        title={isVisible ? "Hide bounding box on canvas" : "Show bounding box on canvas"}
                      >
                        {isVisible ? <Eye size={10} /> : <EyeOff size={10} />}
                        <span>{isVisible ? 'ON' : 'OFF'}</span>
                      </button>
                    </div>
                  </div>

                  {/* Sub-row: Position tag + Property preview pills */}
                  <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '4px', paddingLeft: '4px' }}>
                    <span style={{
                      fontSize: '0.62rem',
                      fontFamily: 'var(--font-mono)',
                      color: 'var(--text-dim)',
                      background: 'var(--bg-dark)',
                      border: '1px solid var(--border-color)',
                      padding: '0.08rem 0.35rem',
                      borderRadius: '4px'
                    }}>
                      pos: {Math.round(node.bbox[1] / 10)}%,{Math.round(node.bbox[0] / 10)}% · {Math.max(1, Math.round((node.bbox[3] - node.bbox[1]) / 10))}×{Math.max(1, Math.round((node.bbox[2] - node.bbox[0]) / 10))}%
                    </span>

                    {node.properties && Object.keys(node.properties).length > 0 &&
                      Object.entries(node.properties).slice(0, 3).map(([k, v]) => (
                        <span
                          key={k}
                          style={{
                            fontSize: '0.62rem',
                            padding: '0.08rem 0.38rem',
                            borderRadius: '4px',
                            background: 'var(--bg-dark)',
                            border: '1px solid var(--border-color)',
                            color: 'var(--text-dim)',
                            fontFamily: 'var(--font-mono)'
                          }}
                        >
                          <span style={{ color: 'var(--text-muted)' }}>{k.replace(/_/g, ' ')}:</span>{' '}
                          <strong style={{ color: 'var(--text-main)', fontWeight: 600 }}>{String(v)}</strong>
                        </span>
                      ))
                    }
                  </div>

                  {/* Action Footer: Ask SAAR in Chat */}
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      marginTop: '2px',
                      paddingTop: '0.35rem',
                      borderTop: '1px solid var(--border-color)',
                      paddingLeft: '4px'
                    }}
                  >
                    <span style={{ fontSize: '0.65rem', color: 'var(--text-dim)' }}>
                      Right-click canvas or ask in chat
                    </span>

                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        if (onAskQuery) {
                          onAskQuery(`Can you explain the causal findings, physical characteristics, and diagnostic relevance of "${node.label}"?`);
                        }
                      }}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '5px',
                        padding: '0.22rem 0.58rem',
                        borderRadius: '6px',
                        background: 'var(--primary-bg)',
                        border: '1px solid var(--primary)',
                        color: 'var(--primary)',
                        fontSize: '0.67rem',
                        fontWeight: 700,
                        cursor: 'pointer',
                        transition: 'all 0.15s ease'
                      }}
                      title="Ask SAAR about this entity in chat"
                    >
                      <MessageSquare size={11} />
                      <span>Ask SAAR</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
        )
      ) : (
        <div style={{
          marginTop: '1rem',
          padding: '1.75rem',
          textAlign: 'center',
          color: 'var(--text-muted)',
          background: 'var(--bg-card)',
          borderRadius: '8px',
          border: '1px dashed var(--border-color)',
          fontSize: '0.78rem'
        }}>
          <Crosshair size={24} style={{ opacity: 0.4, margin: '0 auto 0.5rem auto' }} />
          <div style={{ fontWeight: 600, marginBottom: '0.25rem', color: 'var(--text-main)' }}>No visual objects detected</div>
          <div style={{ fontSize: '0.72rem', opacity: 0.7 }}>
            Visual entities and regional bounding boxes will appear here when an image is analyzed.
          </div>
        </div>
      )}
    </div>
  );
};

export default ImageInspector;
