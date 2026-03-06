'use client';

import { useEffect, useRef } from 'react';

const ORBS = [
  { size: 600, color: 'rgba(108,99,255,0.35)', top: '10%',  left: '15%',  duration: 18, delay: 0  },
  { size: 500, color: 'rgba(167,139,250,0.28)', top: '60%', left: '70%',  duration: 22, delay: -6 },
  { size: 420, color: 'rgba(99,102,241,0.30)',  top: '80%', left: '20%',  duration: 16, delay: -4 },
  { size: 480, color: 'rgba(139,92,246,0.25)',  top: '20%', left: '75%',  duration: 25, delay: -10},
  { size: 350, color: 'rgba(196,181,253,0.22)', top: '45%', left: '45%',  duration: 20, delay: -8 },
];

export default function AnimatedBackground() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Mouse parallax
    const handleMouse = (e: MouseEvent) => {
      const orbs = container.querySelectorAll<HTMLDivElement>('.bg-orb');
      const cx = window.innerWidth / 2;
      const cy = window.innerHeight / 2;
      const dx = (e.clientX - cx) / cx;
      const dy = (e.clientY - cy) / cy;
      orbs.forEach((orb, i) => {
        const factor = (i + 1) * 12;
        orb.style.transform = `translate(${dx * factor}px, ${dy * factor}px)`;
      });
    };
    window.addEventListener('mousemove', handleMouse);
    return () => window.removeEventListener('mousemove', handleMouse);
  }, []);

  return (
    <>
      {/* Inject keyframes */}
      <style>{`
        @keyframes orbFloat {
          0%   { transform: translate(0px, 0px) scale(1);    }
          25%  { transform: translate(60px, -40px) scale(1.05); }
          50%  { transform: translate(-40px, 60px) scale(0.95); }
          75%  { transform: translate(50px, 30px) scale(1.03);  }
          100% { transform: translate(0px, 0px) scale(1);    }
        }
        @keyframes gridPulse {
          0%, 100% { opacity: 0.35; }
          50%       { opacity: 0.18; }
        }
        .bg-orb {
          transition: transform 1.5s cubic-bezier(0.25, 0.46, 0.45, 0.94);
          will-change: transform;
        }
      `}</style>

      <div
        ref={containerRef}
        style={{
          position: 'fixed',
          inset: 0,
          zIndex: 0,
          overflow: 'hidden',
          pointerEvents: 'none',
        }}
      >
        {/* Floating orbs */}
        {ORBS.map((orb, i) => (
          <div
            key={i}
            className="bg-orb"
            style={{
              position: 'absolute',
              top: orb.top,
              left: orb.left,
              width: orb.size,
              height: orb.size,
              borderRadius: '50%',
              background: `radial-gradient(circle at 40% 40%, ${orb.color} 0%, transparent 65%)`,
              filter: 'blur(40px)',
              animation: `orbFloat ${orb.duration}s ease-in-out ${orb.delay}s infinite`,
              transform: 'translate(-50%, -50%)',
            }}
          />
        ))}

        {/* Dot grid */}
        <div style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: 'radial-gradient(rgba(108,99,255,0.2) 1px, transparent 1px)',
          backgroundSize: '44px 44px',
          animation: 'gridPulse 4s ease-in-out infinite',
        }} />

        {/* Top gradient beam */}
        <div style={{
          position: 'absolute',
          top: '-20%',
          left: '30%',
          width: '40%',
          height: '60%',
          background: 'radial-gradient(ellipse, rgba(108,99,255,0.12) 0%, transparent 70%)',
          filter: 'blur(60px)',
          animation: 'orbFloat 30s ease-in-out -5s infinite',
        }} />
      </div>
    </>
  );
}
