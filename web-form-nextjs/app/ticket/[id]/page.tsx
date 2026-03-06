'use client';

import TicketStatus from '@/components/TicketStatus';
import AnimatedBackground from '@/components/AnimatedBackground';
import Link from 'next/link';

interface TicketPageProps {
  params: { id: string };
}

export default function TicketPage({ params }: TicketPageProps) {
  const ticketId = decodeURIComponent(params.id).toUpperCase();

  return (
    <>
      <AnimatedBackground />
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '40px 16px',
        position: 'relative',
        zIndex: 1,
      }}>
        <div style={{ width: '100%', maxWidth: 640 }}>

          {/* Back link */}
          <Link href="/" style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            color: 'rgba(255,255,255,0.4)', fontSize: 13, fontWeight: 600,
            textDecoration: 'none', marginBottom: 32,
            transition: 'color 0.2s',
          }}>
            ← Back to Support
          </Link>

          {/* Header */}
          <div style={{ marginBottom: 32, textAlign: 'center' }}>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              background: 'rgba(168,85,247,0.15)', color: '#c084fc',
              border: '1px solid rgba(168,85,247,0.3)', borderRadius: 100,
              padding: '6px 16px', fontSize: 12, fontWeight: 600,
              letterSpacing: 0.3, marginBottom: 20,
            }}>
              📍 Ticket Tracker
            </div>
            <h1 style={{
              fontSize: 'clamp(28px, 5vw, 44px)',
              fontWeight: 900,
              background: 'linear-gradient(135deg, #a78bfa 0%, #c4b5fd 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              marginBottom: 10,
              letterSpacing: '-0.5px',
            }}>
              Ticket Status
            </h1>
            <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: 15 }}>
              Real-time status for <span style={{ color: '#a78bfa', fontWeight: 700, fontFamily: 'monospace' }}>{ticketId}</span>
            </p>
          </div>

          <TicketStatus ticketId={ticketId} />

          {/* Footer */}
          <div style={{ marginTop: 40, textAlign: 'center', fontSize: 12, color: 'rgba(255,255,255,0.2)' }}>
            © 2026 NovaDeskAI · Built with ❤️ and AI
          </div>
        </div>
      </div>
    </>
  );
}
