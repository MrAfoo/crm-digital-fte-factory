'use client';

import { useEffect, useRef } from 'react';

interface Particle {
  x: number;
  y: number;
  size: number;
  speedY: number;
  speedX: number;
  opacity: number;
  fadeSpeed: number;
  color: string;
  life: number;
  maxLife: number;
}

const COLORS = [
  'rgba(139,92,246,',   // violet
  'rgba(109,40,217,',   // purple
  'rgba(99,102,241,',   // indigo
  'rgba(167,139,250,',  // light violet
  'rgba(196,181,253,',  // lavender
];

export default function AnimatedBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<Particle[]>([]);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resize = () => {
      canvas.width  = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    const PARTICLE_COUNT = 80;

    const createParticle = (fromBottom = false): Particle => {
      const maxLife = 120 + Math.random() * 180;
      return {
        x: Math.random() * window.innerWidth,
        y: fromBottom ? window.innerHeight + 10 : Math.random() * window.innerHeight,
        size: 1 + Math.random() * 2.5,
        speedY: -(0.3 + Math.random() * 0.7),
        speedX: (Math.random() - 0.5) * 0.3,
        opacity: 0,
        fadeSpeed: 0.008 + Math.random() * 0.012,
        color: COLORS[Math.floor(Math.random() * COLORS.length)],
        life: fromBottom ? 0 : Math.random() * maxLife,
        maxLife,
      };
    };

    // Init particles spread across screen
    particlesRef.current = Array.from({ length: PARTICLE_COUNT }, () => createParticle(false));

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      particlesRef.current.forEach((p, i) => {
        p.life += 1;
        p.x += p.speedX;
        p.y += p.speedY;

        // Fade in first quarter, fade out last quarter
        const progress = p.life / p.maxLife;
        if (progress < 0.25) {
          p.opacity = Math.min(p.opacity + p.fadeSpeed * 2, 0.7);
        } else if (progress > 0.75) {
          p.opacity = Math.max(p.opacity - p.fadeSpeed * 2, 0);
        }

        // Draw particle with glow
        if (p.opacity > 0.01) {
          // Outer glow
          const glow = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.size * 4);
          glow.addColorStop(0, `${p.color}${p.opacity * 0.6})`);
          glow.addColorStop(1, `${p.color}0)`);
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.size * 4, 0, Math.PI * 2);
          ctx.fillStyle = glow;
          ctx.fill();

          // Core dot
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
          ctx.fillStyle = `${p.color}${p.opacity})`;
          ctx.fill();
        }

        // Respawn when dead or off screen
        if (p.life >= p.maxLife || p.y < -10 || p.x < -10 || p.x > canvas.width + 10) {
          particlesRef.current[i] = createParticle(true);
        }
      });

      rafRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener('resize', resize);
    };
  }, []);

  return (
    <>
      <style>{`
        @keyframes gridFade {
          0%, 100% { opacity: 0.05; }
          50%       { opacity: 0.025; }
        }
      `}</style>
      <div style={{ position: 'fixed', inset: 0, zIndex: 0, background: '#07070f', pointerEvents: 'none' }}>
        {/* Canvas for particles */}
        <canvas
          ref={canvasRef}
          style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}
        />
        {/* Subtle dot grid */}
        <div style={{
          position: 'absolute', inset: 0,
          backgroundImage: 'radial-gradient(rgba(139,92,246,0.15) 1px, transparent 1px)',
          backgroundSize: '48px 48px',
          animation: 'gridFade 6s ease-in-out infinite',
        }} />
      </div>
    </>
  );
}
