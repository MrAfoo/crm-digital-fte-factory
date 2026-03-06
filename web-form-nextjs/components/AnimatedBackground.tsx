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
        @keyframes shimmer {
          0%, 100% { opacity: 0.6; }
          50%       { opacity: 1; }
        }
        @keyframes gridFade {
          0%, 100% { opacity: 0.12; }
          50%       { opacity: 0.06; }
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

        {/* Aurora wave 1 — large violet blob top-left */}
        <div style={{
          position: 'absolute',
          top: '-20%',
          left: '-10%',
          width: '70vw',
          height: '70vw',
          borderRadius: '40% 60% 70% 30% / 40% 50% 60% 50%',
          background: 'radial-gradient(ellipse at 50% 50%, rgba(108,63,255,0.55) 0%, rgba(108,63,255,0.2) 40%, transparent 70%)',
          filter: 'blur(60px)',
          animation: 'aurora1 18s ease-in-out infinite',
        }} />

        {/* Aurora wave 2 — indigo blob bottom-right */}
        <div style={{
          position: 'absolute',
          bottom: '-15%',
          right: '-10%',
          width: '65vw',
          height: '65vw',
          borderRadius: '60% 40% 30% 70% / 50% 60% 40% 50%',
          background: 'radial-gradient(ellipse at 50% 50%, rgba(79,70,229,0.50) 0%, rgba(79,70,229,0.18) 40%, transparent 70%)',
          filter: 'blur(70px)',
          animation: 'aurora2 24s ease-in-out infinite',
        }} />

        {/* Aurora wave 3 — violet/pink center */}
        <div style={{
          position: 'absolute',
          top: '30%',
          left: '25%',
          width: '50vw',
          height: '50vw',
          borderRadius: '50% 50% 40% 60% / 60% 40% 60% 40%',
          background: 'radial-gradient(ellipse at 50% 50%, rgba(167,59,255,0.35) 0%, rgba(139,92,246,0.15) 40%, transparent 70%)',
          filter: 'blur(80px)',
          animation: 'aurora3 30s ease-in-out infinite',
        }} />

        {/* Aurora wave 4 — deep blue accent top-right */}
        <div style={{
          position: 'absolute',
          top: '-10%',
          right: '5%',
          width: '45vw',
          height: '45vw',
          borderRadius: '30% 70% 60% 40% / 50% 40% 60% 50%',
          background: 'radial-gradient(ellipse at 50% 50%, rgba(56,189,248,0.22) 0%, rgba(56,189,248,0.08) 40%, transparent 70%)',
          filter: 'blur(60px)',
          animation: 'aurora4 20s ease-in-out infinite',
        }} />

        {/* Aurora wave 5 — warm purple bottom-left */}
        <div style={{
          position: 'absolute',
          bottom: '5%',
          left: '5%',
          width: '40vw',
          height: '40vw',
          borderRadius: '70% 30% 50% 50% / 40% 60% 40% 60%',
          background: 'radial-gradient(ellipse at 50% 50%, rgba(192,38,211,0.28) 0%, rgba(192,38,211,0.10) 40%, transparent 70%)',
          filter: 'blur(55px)',
          animation: 'aurora1 22s ease-in-out -8s infinite',
        }} />

        {/* Subtle shimmer overlay */}
        <div style={{
          position: 'absolute',
          inset: 0,
          background: 'linear-gradient(135deg, rgba(108,63,255,0.04) 0%, transparent 50%, rgba(79,70,229,0.04) 100%)',
          animation: 'shimmer 8s ease-in-out infinite',
        }} />

        {/* Dot grid */}
        <div style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: 'radial-gradient(rgba(167,139,250,0.25) 1px, transparent 1px)',
          backgroundSize: '44px 44px',
          animation: 'gridFade 6s ease-in-out infinite',
        }} />

      </div>
    </>
  );
}
