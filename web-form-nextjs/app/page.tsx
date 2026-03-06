'use client';

import SupportForm from '@/components/SupportForm';

export default function Home() {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px 16px' }}>
      <div style={{ width: '100%', maxWidth: 640 }}>

        {/* Hero Section */}
        <div style={{ textAlign: 'center', marginBottom: 48 }}>
          {/* Badge */}
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 8,
            background: 'rgba(168, 85, 247, 0.15)', color: '#c084fc',
            border: '1px solid rgba(168, 85, 247, 0.3)', borderRadius: 100,
            padding: '6px 16px', fontSize: 12, fontWeight: 600, letterSpacing: 0.3,
            marginBottom: 24
          }}>
            <span>⚡</span>
            Powered by Nova AI
          </div>

          {/* H1 with gradient */}
          <h1 style={{
            fontSize: 'clamp(32px, 6vw, 56px)',
            fontWeight: 900,
            background: 'linear-gradient(135deg, #a78bfa 0%, #c4b5fd 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            marginBottom: 16,
            letterSpacing: '-0.8px',
          }}>
            Customer Support
          </h1>

          {/* Subtitle */}
          <p style={{
            fontSize: 16,
            color: 'rgba(255, 255, 255, 0.6)',
            marginBottom: 32,
            maxWidth: 500,
            margin: '0 auto 32px',
            lineHeight: 1.6,
          }}>
            Get instant AI-powered support. Nova responds in under 2 minutes.
          </p>

          {/* Feature Pills */}
          <div style={{
            display: 'flex',
            gap: 12,
            justifyContent: 'center',
            flexWrap: 'wrap',
            marginBottom: 48,
          }}>
            {[
              { icon: '🤖', text: 'AI-Powered' },
              { icon: '⚡', text: '< 2 min reply' },
              { icon: '🔒', text: 'Secure' },
            ].map((feature, idx) => (
              <div
                key={idx}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 6,
                  background: 'rgba(255, 255, 255, 0.06)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: 12,
                  padding: '8px 14px',
                  fontSize: 13,
                  fontWeight: 600,
                  color: 'rgba(255, 255, 255, 0.8)',
                }}
              >
                <span>{feature.icon}</span>
                {feature.text}
              </div>
            ))}
          </div>
        </div>

        {/* Form Component */}
        <SupportForm />

        {/* Footer */}
        <div style={{
          marginTop: 40,
          textAlign: 'center',
          fontSize: 13,
          color: 'rgba(255, 255, 255, 0.35)',
        }}>
          © 2026 NovaDeskAI · Built with ❤️ and AI
        </div>

      </div>
    </div>
  );
}
