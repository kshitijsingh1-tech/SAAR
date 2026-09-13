import React from 'react';
import {
  Chart as ChartJS,
  RadialLinearScale,
  ArcElement,
  Tooltip,
  Legend
} from 'chart.js';
import { PolarArea } from 'react-chartjs-2';
import { PieChart, Activity, Sparkles } from 'lucide-react';

// Register Chart.js components required for Polar Area chart
ChartJS.register(RadialLinearScale, ArcElement, Tooltip, Legend);

/**
 * PerformancePolarArea (Section 29)
 * High-fidelity Chart.js Polar Area chart rendering multi-dimensional performance
 * profiles (Coverage, Speed, Overhead Reach, Shot Variety, Quality, Kinematic Precision).
 */
export function PerformanceRadar({ result }) {
  if (!result) return null;

  const quality = result.quality;
  const court = result.court_metrics;
  const movement = result.movement_metrics;
  const pose = result.pose_metrics;
  const shotMetrics = result.shot_metrics;
  const isCalibrated = Boolean(result.court_calibration?.is_calibrated);

  // Derive standardized 0-100 scores from backend metrics
  const coverageScore = isCalibrated && court?.court_coverage_pct
    ? Math.min(100, Math.round((court.court_coverage_pct / 50.0) * 100))
    : (court?.player_heat_distribution ? 70 : 50);

  const speedScore = isCalibrated && movement?.average_speed_m_s
    ? Math.min(100, Math.round((movement.average_speed_m_s / 2.5) * 100))
    : (movement?.distance_travelled_m ? 75 : 60);

  const elbowAngle = pose?.mean_contact_elbow_deg ?? pose?.elbow_extension_deg;
  const overheadExtensionScore = elbowAngle
    ? Math.min(100, Math.round((elbowAngle / 165.0) * 100))
    : 78;

  const shotTypeCount = Object.keys(shotMetrics?.count_by_shot_type || {}).length;
  const shotVarietyScore = Math.min(100, Math.max(30, shotTypeCount * 22));

  const qualityScore = quality?.confidence === 'HIGH'
    ? 95
    : (quality?.confidence === 'MEDIUM' ? 75 : 55);

  const stabilityScore = quality?.camera_stability_score !== undefined && quality?.camera_stability_score !== null
    ? Math.round(quality.camera_stability_score * 100)
    : 88;

  const labels = [
    'Court Coverage',
    'Movement Speed',
    'Overhead Extension',
    'Shot Variety',
    'Capture Quality',
    'Camera Stability'
  ];

  const dataValues = [
    coverageScore,
    speedScore,
    overheadExtensionScore,
    shotVarietyScore,
    qualityScore,
    stabilityScore
  ];

  const chartData = {
    labels,
    datasets: [
      {
        label: 'Performance Score (0-100)',
        data: dataValues,
        backgroundColor: [
          'rgba(2, 132, 199, 0.70)',   // Ocean Sky Blue
          'rgba(99, 102, 241, 0.70)',  // Indigo
          'rgba(16, 185, 129, 0.70)',  // Emerald Green
          'rgba(245, 158, 11, 0.70)',  // Amber / Gold
          'rgba(236, 72, 153, 0.70)',  // Rose Pink
          'rgba(20, 184, 166, 0.70)'   // Teal
        ],
        borderColor: [
          '#0284c7',
          '#6366f1',
          '#10b981',
          '#f59e0b',
          '#ec4899',
          '#14b8a6'
        ],
        borderWidth: 1.5,
        hoverBackgroundColor: [
          'rgba(2, 132, 199, 0.90)',
          'rgba(99, 102, 241, 0.90)',
          'rgba(16, 185, 129, 0.90)',
          'rgba(245, 158, 11, 0.90)',
          'rgba(236, 72, 153, 0.90)',
          'rgba(20, 184, 166, 0.90)'
        ]
      }
    ]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
      animateRotate: true,
      animateScale: true,
      duration: 800
    },
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          boxWidth: 10,
          boxHeight: 10,
          padding: 10,
          font: {
            size: 11,
            family: "'Inter', sans-serif",
            weight: '600'
          },
          color: '#475569'
        }
      },
      tooltip: {
        backgroundColor: 'rgba(15, 23, 42, 0.92)',
        titleFont: { size: 12, weight: '700' },
        bodyFont: { size: 12, weight: '600' },
        padding: 10,
        cornerRadius: 8,
        callbacks: {
          label: (context) => ` Score: ${context.parsed.r}/100`
        }
      }
    },
    scales: {
      r: {
        min: 0,
        max: 100,
        ticks: {
          stepSize: 25,
          color: '#94a3b8',
          backdropColor: 'transparent',
          font: {
            size: 9,
            family: 'monospace'
          }
        },
        grid: {
          color: 'rgba(226, 232, 240, 0.85)'
        },
        angleLines: {
          color: 'rgba(226, 232, 240, 0.85)'
        },
        pointLabels: {
          display: false
        }
      }
    }
  };

  return (
    <div
      className="performance-polar-container"
      style={{
        background: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: '16px',
        padding: '18px 20px',
        boxShadow: '0 4px 20px -2px rgba(0,0,0,0.04)',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px'
      }}
    >
      <div style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ background: '#f0f9ff', color: '#0284c7', padding: '6px', borderRadius: '8px', display: 'flex' }}>
            <PieChart size={16} />
          </div>
          <div>
            <h4 style={{ margin: 0, fontSize: '0.94rem', fontWeight: '800', color: '#0f172a' }}>
              Performance Polar Profile
            </h4>
            <div style={{ fontSize: '0.70rem', color: '#64748b' }}>
              Multi-axial biomechanical and capture dimension breakdown
            </div>
          </div>
        </div>
      </div>

      <div style={{ position: 'relative', width: '100%', height: '270px' }}>
        <PolarArea data={chartData} options={chartOptions} />
      </div>
    </div>
  );
}

export const PerformancePolarArea = PerformanceRadar;

