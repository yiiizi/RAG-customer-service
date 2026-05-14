/**
 * Simple SVG-based CAPTCHA component.
 * Generates a random alphanumeric code rendered as an SVG with noise lines.
 * No external dependencies required.
 * 支持深色/浅色主题自适应
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { useThemeStore } from '@/stores/useThemeStore';

interface CaptchaProps {
  onChange: (code: string) => void;
  height?: number;
  width?: number;
}

const CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'; // Excludes easily confused: I/O/0/1
const CODE_LENGTH = 4;

function randomChar(): string {
  return CHARS[Math.floor(Math.random() * CHARS.length)];
}

function generateCode(): string {
  return Array.from({ length: CODE_LENGTH }, randomChar).join('');
}

const Captcha: React.FC<CaptchaProps> = ({ onChange, height = 40, width = 120 }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [code, setCode] = useState(() => generateCode());
  const isDark = useThemeStore((s) => s.resolvedMode === 'dark');

  const draw = useCallback(
    (text: string) => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      // Background
      ctx.fillStyle = isDark ? '#12122A' : '#f5f5f5';
      ctx.fillRect(0, 0, width, height);

      // Border
      ctx.strokeStyle = isDark ? '#4A4A6A' : '#d9d9d9';
      ctx.lineWidth = 1;
      ctx.strokeRect(0, 0, width, height);

      // Noise lines
      for (let i = 0; i < 4; i++) {
        ctx.strokeStyle = isDark
          ? `hsl(${Math.random() * 60 + 240}, 50%, 50%)`
          : `hsl(${Math.random() * 360}, 40%, 70%)`;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(Math.random() * width, Math.random() * height);
        ctx.lineTo(Math.random() * width, Math.random() * height);
        ctx.stroke();
      }

      // Noise dots
      for (let i = 0; i < 30; i++) {
        ctx.fillStyle = isDark
          ? `hsl(${Math.random() * 60 + 240}, 40%, 50%)`
          : `hsl(${Math.random() * 360}, 40%, 60%)`;
        ctx.fillRect(Math.random() * width, Math.random() * height, 2, 2);
      }

      // Characters
      const charWidth = width / (text.length + 1);
      for (let i = 0; i < text.length; i++) {
        ctx.save();
        ctx.font = `bold ${height * 0.6}px monospace`;
        ctx.fillStyle = isDark
          ? `hsl(${Math.random() * 60 + 240}, 70%, 75%)`
          : `hsl(${Math.random() * 360}, 70%, 35%)`;
        ctx.translate(charWidth * (i + 0.7), height * 0.7);
        ctx.rotate(((Math.random() - 0.5) * 30 * Math.PI) / 180);
        ctx.fillText(text[i], 0, 0);
        ctx.restore();
      }
    },
    [width, height, isDark],
  );

  useEffect(() => {
    draw(code);
    onChange(code);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [code, draw]);

  const refresh = () => {
    setCode(generateCode());
  };

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      onClick={refresh}
      title="点击刷新验证码"
      style={{
        cursor: 'pointer',
        borderRadius: 6,
        border: `1px solid ${isDark ? '#4A4A6A' : '#d9d9d9'}`,
        verticalAlign: 'middle',
      }}
    />
  );
};

export default Captcha;
