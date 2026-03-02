import SupportForm from '@/components/SupportForm';

export default function Home() {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '24px 16px' }}>
      <div style={{ width: '100%', maxWidth: 580 }}>

        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
            <div style={{
              width: 48, height: 48, borderRadius: 14,
              background: 'linear-gradient(135deg, #6C63FF, #a78bfa)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 24, boxShadow: '0 8px 24px rgba(108,99,255,0.4)',
            }}>🤖</div>
            <h1 style={{
              fontSize: 32, fontWeight: 800, color: '#fff', letterSpacing: '-0.5px',
              background: 'linear-gradient(135deg, #6C63FF, #a78bfa)',
              WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            }}>
              NovaDeskAI
            </h1>
          </div>
          <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: 14, marginBottom: 12 }}>
            AI-Powered Customer Success · Available 24/7
          </p>
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            background: 'rgba(16,185,129,0.12)', color: '#10b981',
            border: '1px solid rgba(16,185,129,0.25)', borderRadius: 100,
            padding: '4px 14px', fontSize: 11, fontWeight: 600, letterSpacing: 0.3,
          }}>
            <span style={{
              width: 6, height: 6, borderRadius: '50%', background: '#10b981',
              animation: 'blink 2s ease-in-out infinite', display: 'inline-block',
            }}/>
            All systems operational
          </div>
        </div>

        {/* Form */}
        <SupportForm />

        {/* Footer */}
        <div style={{
          marginTop: 24, textAlign: 'center', fontSize: 11,
          color: 'rgba(255,255,255,0.2)', display: 'flex',
          justifyContent: 'space-between', alignItems: 'center',
        }}>
          <span>Powered by <span style={{ color: '#6C63FF', fontWeight: 600 }}>NovaDeskAI</span></span>
          <span>⚡ Avg reply &lt; 2 min · 99.9% uptime</span>
        </div>
      </div>
    </div>
  );
}
