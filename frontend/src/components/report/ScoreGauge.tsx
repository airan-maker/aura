/**
 * Score gauge visualization using Canvas
 */

'use client';

import React, { useEffect, useRef } from 'react';

interface ScoreGaugeProps {
  score: number;
  label: string;
  className?: string;
}

export function ScoreGauge({ score, label, className = '' }: ScoreGaugeProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = 80;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Background arc
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, 0.75 * Math.PI, 2.25 * Math.PI);
    ctx.lineWidth = 20;
    ctx.strokeStyle = '#e5e7eb';
    ctx.stroke();

    // Score arc
    const endAngle = 0.75 * Math.PI + (score / 100) * 1.5 * Math.PI;
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, 0.75 * Math.PI, endAngle);
    ctx.lineWidth = 20;

    // Color based on score
    if (score >= 80) {
      ctx.strokeStyle = '#22c55e'; // green
    } else if (score >= 60) {
      ctx.strokeStyle = '#eab308'; // yellow
    } else {
      ctx.strokeStyle = '#ef4444'; // red
    }
    ctx.stroke();

    // Score text
    ctx.font = 'bold 36px sans-serif';
    ctx.fillStyle = '#1f2937';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(score.toFixed(0), centerX, centerY);

  }, [score]);

  const getScoreColor = () => {
    if (score >= 80) return 'text-success-600';
    if (score >= 60) return 'text-warning-600';
    return 'text-danger-600';
  };

  const getScoreLabel = () => {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Fair';
    return 'Poor';
  };

  return (
    <div className={`flex flex-col items-center ${className}`}>
      <canvas ref={canvasRef} width={200} height={200} />
      <h3 className="text-lg font-semibold text-gray-900 mt-2">{label}</h3>
      <p className={`text-sm font-medium ${getScoreColor()}`}>{getScoreLabel()}</p>
    </div>
  );
}
