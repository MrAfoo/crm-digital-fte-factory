'use client';

export default function AnimatedBackground() {
  return (
    <>
      <style>{`
        @keyframes aurora1 {
          0%   { transform: translate(0%, 0%) rotate(0deg) scale(1); }
          25%  { transform: translate(5%, -8%) rotate(15deg) scale(1.1); }
          50%  { transform: translate(-8%, 5%) rotate(-10deg) scale(0.95); }
          75%  { transform: translate(8%, 8%) rotate(20deg) scale(1.05); }
          100% { transform: translate(0%, 0%) rotate(0deg) scale(1); }
        }
        @keyframes aurora2 {
          0%   { transform: translate(0%, 0%) rotate(0deg) scale(1); }
          33%  { transform: translate(-10%, 8%) rotate(-20deg) scale(1.15); }
          66%  { transform: translate(10%, -5%) rotate(15deg) scale(0.9); }
          100% { transform: translate(0%, 0%) rotate(0deg) scale(1); }
        }
        @keyframes aurora3 {
          0%   { transform: translate(0%, 0%) rotate(0deg) scale(1); }
          20%  { transform: translate(8%, 10%) rotate(10deg) scale(1.1); }
          40%  { transform: translate(-5%, -8%) rotate(-15deg) scale(0.92); }
          60%  { transform: translate(-10%, 5%) rotate(20deg) scale(1.08); }
          80%  { transform: translate(5%, -10%) rotate(-5deg) scale(0.97); }
          100% { transform: translate(0%, 0%) rotate(0deg) scale(1); }
        }
        @keyframes aurora4 {
          0%   { transform: translate(0%, 0%) rotate(0deg) scale(1); }
          50%  { transform: translate(-8%, -8%) rotate(-25deg) scale(1.2); }
          100% { transform: translate(0%, 0%) rotate(0deg) scale(1); }
        }
        @keyframes gridFade {
          0%, 100% { opacity: 0.06; }
          50%       { opacity: 0.03; }
        }
      `}</style>

      <div style={{
        position: 'fixed',
        inset: 0,
        zIndex: 0,
        overflow: 'hidden',
        pointerEvents: 'none',
        background: '#07070f',
      }}>

        {/* Wave 1 — deep violet, top-left */}
        <div style={{
          position: 'absolute',
          top: '-25%',
          left: '-15%',
          width: '70vw',
          height: '70vw',
          borderRadius: '40% 60% 70% 30% / 40% 50% 60% 50%',
          background: 'radial-gradient(ellipse at 50% 50%, rgba(72,40,180,0.18) 0%, rgba(72,40,180,0.06) 50%, transparent 70%)',
          filter: 'blur(80px)',
          animation: 'aurora1 22s ease-in-out infinite',
        }} />

        {/* Wave 2 — indigo, bottom-right */}
        <div style={{
          position: 'absolute',
          bottom: '-20%',
          right: '-15%',
          width: '65vw',
          height: '65vw',
          borderRadius: '60% 40% 30% 70% / 50% 60% 40% 50%',
          background: 'radial-gradient(ellipse at 50% 50%, rgba(49,46,129,0.16) 0%, rgba(49,46,129,0.05) 50%, transparent 70%)',
          filter: 'blur(90px)',
          animation: 'aurora2 28s ease-in-out infinite',
        }} />

        {/* Wave 3 — purple, center */}
        <div style={{
          position: 'absolute',
          top: '35%',
          left: '20%',
          width: '55vw',
          height: '55vw',
          borderRadius: '50% 50% 40% 60% / 60% 40% 60% 40%',
          background: 'radial-gradient(ellipse at 50% 50%, rgba(88,28,135,0.14) 0%, rgba(88,28,135,0.04) 50%, transparent 70%)',
          filter: 'blur(100px)',
          animation: 'aurora3 35s ease-in-out infinite',
        }} />

        {/* Wave 4 — dark blue, top-right */}
        <div style={{
          position: 'absolute',
          top: '-15%',
          right: '0%',
          width: '50vw',
          height: '50vw',
          borderRadius: '30% 70% 60% 40% / 50% 40% 60% 50%',
          background: 'radial-gradient(ellipse at 50% 50%, rgba(30,27,75,0.20) 0%, rgba(30,27,75,0.06) 50%, transparent 70%)',
          filter: 'blur(70px)',
          animation: 'aurora4 24s ease-in-out infinite',
        }} />

        {/* Wave 5 — muted magenta, bottom-left */}
        <div style={{
          position: 'absolute',
          bottom: '0%',
          left: '0%',
          width: '45vw',
          height: '45vw',
          borderRadius: '70% 30% 50% 50% / 40% 60% 40% 60%',
          background: 'radial-gradient(ellipse at 50% 50%, rgba(76,29,149,0.12) 0%, rgba(76,29,149,0.04) 50%, transparent 70%)',
          filter: 'blur(85px)',
          animation: 'aurora1 26s ease-in-out -10s infinite',
        }} />

        {/* Very subtle dot grid */}
        <div style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: 'radial-gradient(rgba(139,92,246,0.12) 1px, transparent 1px)',
          backgroundSize: '48px 48px',
          animation: 'gridFade 8s ease-in-out infinite',
        }} />

      </div>
    </>
  );
}
