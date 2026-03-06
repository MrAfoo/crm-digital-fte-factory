'use client';

import { useEffect, useRef } from 'react';
import { gsap } from 'gsap';

interface Orb {
  el: HTMLDivElement;
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
}

export default function AnimatedBackground() {
  const canvasRef = useRef<HTMLDivElement>(null);
  const orbsRef  = useRef<Orb[]>([]);
  const rafRef   = useRef<number>(0);

  useEffect(() => {
    const container = canvasRef.current;
    if (!container) return;

    const W = window.innerWidth;
    const H = window.innerHeight;

    const ORB_CONFIG = [
      { color: 'rgba(108,99,255,0.18)', size: 520 },
      { color: 'rgba(167,139,250,0.12)', size: 420 },
      { color: 'rgba(99,102,241,0.15)',  size: 380 },
      { color: 'rgba(139,92,246,0.10)',  size: 460 },
      { color: 'rgba(196,181,253,0.08)', size: 300 },
    ];

    // Create orbs
    orbsRef.current = ORB_CONFIG.map(cfg => {
      const el = document.createElement('div');
      const x = Math.random() * W;
      const y = Math.random() * H;
      Object.assign(el.style, {
        position: 'absolute',
        width:  `${cfg.size}px`,
        height: `${cfg.size}px`,
        borderRadius: '50%',
        background: `radial-gradient(circle, ${cfg.color} 0%, transparent 70%)`,
        transform: `translate(${x - cfg.size/2}px, ${y - cfg.size/2}px)`,
        pointerEvents: 'none',
        willChange: 'transform',
        filter: 'blur(2px)',
      });
      container.appendChild(el);

      // Drift animation via GSAP
      const tl = gsap.timeline({ repeat: -1, yoyo: true });
      tl.to(el, {
        x: (Math.random() - 0.5) * 300,
        y: (Math.random() - 0.5) * 200,
        duration: 8 + Math.random() * 12,
        ease: 'sine.inOut',
      }).to(el, {
        x: (Math.random() - 0.5) * 300,
        y: (Math.random() - 0.5) * 200,
        duration: 8 + Math.random() * 12,
        ease: 'sine.inOut',
      });

      return { el, x, y, vx: 0, vy: 0, size: cfg.size };
    });

    // Subtle mouse parallax
    const handleMouse = (e: MouseEvent) => {
      const mx = (e.clientX / W - 0.5) * 30;
      const my = (e.clientY / H - 0.5) * 20;
      orbsRef.current.forEach((orb, i) => {
        const factor = 0.3 + i * 0.15;
        gsap.to(orb.el, {
          x: `+=${mx * factor * 0.1}`,
          y: `+=${my * factor * 0.1}`,
          duration: 2,
          ease: 'power1.out',
          overwrite: 'auto',
        });
      });
    };
    window.addEventListener('mousemove', handleMouse);

    // Animated grid dots
    const grid = document.createElement('div');
    Object.assign(grid.style, {
      position: 'absolute', inset: '0',
      backgroundImage: 'radial-gradient(rgba(108,99,255,0.15) 1px, transparent 1px)',
      backgroundSize: '48px 48px',
      opacity: '0.4',
      pointerEvents: 'none',
    });
    container.appendChild(grid);
    gsap.to(grid, { opacity: 0.25, duration: 3, repeat: -1, yoyo: true, ease: 'sine.inOut' });

    return () => {
      window.removeEventListener('mousemove', handleMouse);
      gsap.killTweensOf(orbsRef.current.map(o => o.el));
      gsap.killTweensOf(grid);
      cancelAnimationFrame(rafRef.current);
      container.innerHTML = '';
    };
  }, []);

  return (
    <div
      ref={canvasRef}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 0,
        overflow: 'hidden',
        pointerEvents: 'none',
      }}
    />
  );
}
