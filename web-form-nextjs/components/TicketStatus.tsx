'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { gsap } from 'gsap';

interface Ticket {
  ticket_id: string;
  name: string;
  email: string;
  subject: string;
  channel: string;
  description: string;
  status: 'open' | 'in_progress' | 'resolved' | 'escalated';
  nova_response?: string;
  sentiment?: string;
  created_at: string;
  responded_at?: string;
}

const STATUS_CONFIG = {
  open:        { label: 'Open',        color: '#60a5fa', bg: 'rgba(96,165,250,0.12)',  icon: '📋' },
  in_progress: { label: 'Processing…', color: '#fbbf24', bg: 'rgba(251,191,36,0.12)',  icon: '⚡' },
  resolved:    { label: 'Resolved',    color: '#34d399', bg: 'rgba(52,211,153,0.12)',  icon: '✅' },
  escalated:   { label: 'Escalated',   color: '#f87171', bg: 'rgba(248,113,113,0.12)', icon: '🔺' },
};

const CHANNEL_ICON: Record<string, string> = {
  web: '🌐', email: '📧', whatsapp: '💬', gmail: '📧',
};

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function TicketStatus({ ticketId }: { ticketId: string }) {
  const [ticket, setTicket]   = useState<Ticket | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState('');
  const cardRef  = useRef<HTMLDivElement>(null);
  const pollRef  = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchTicket = useCallback(async (animate = false) => {
    try {
      const res = await fetch(`${API_BASE}/api/tickets/${ticketId}`, { cache: 'no-store' });
      if (!res.ok) throw new Error(res.status === 404 ? `Ticket ${ticketId} not found` : `Error ${res.status}`);
      const data: Ticket = await res.json();
      setTicket(data);
      setError('');
      if (animate && cardRef.current) {
        gsap.fromTo(cardRef.current, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.6, ease: 'power3.out' });
      }
      // Stop polling once resolved or escalated
      if ((data.status === 'resolved' || data.status === 'escalated') && pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong');
    } finally {
      setLoading(false);
    }
  }, [ticketId]);

  useEffect(() => {
    fetchTicket(true);
    // Auto-refresh every 3s while ticket is in_progress
    pollRef.current = setInterval(() => fetchTicket(false), 3000);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [fetchTicket]);

  // ── Loading ────────────────────────────────────────────────
  if (loading) return (
    <div className="glass rounded-3xl" style={{ padding: '60px 40px', textAlign: 'center' }}>
      <svg className="spinner" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="url(#grad)" strokeWidth="2" style={{ margin: '0 auto 20px' }}>
        <defs><linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#6C63FF"/><stop offset="100%" stopColor="#a78bfa"/></linearGradient></defs>
        <circle cx="12" cy="12" r="10" strokeOpacity="0.2"/>
        <path d="M12 2a10 10 0 0 1 10 10" stroke="#a78bfa"/>
      </svg>
      <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: 14 }}>Loading ticket…</p>
    </div>
  );

  // ── Error ──────────────────────────────────────────────────
  if (error) return (
    <div className="glass rounded-3xl" style={{ padding: '60px 40px', textAlign: 'center' }}>
      <div style={{ fontSize: 48, marginBottom: 20 }}>🔍</div>
      <h3 style={{ fontSize: 20, fontWeight: 700, color: '#fff', marginBottom: 10 }}>Ticket not found</h3>
      <p style={{ color: 'rgba(255,255,255,0.4)', marginBottom: 28, fontSize: 14 }}>{error}</p>
      <a href="/" className="nova-btn" style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 8 }}>
        ← Submit a New Ticket
      </a>
    </div>
  );

  if (!ticket) return null;
  const st = STATUS_CONFIG[ticket.status] || STATUS_CONFIG.open;

  // ── Ticket card ────────────────────────────────────────────
  return (
    <div ref={cardRef} style={{ opacity: 0 }}>

      {/* Status header */}
      <div className="glass rounded-3xl" style={{ padding: '28px 32px', marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div style={{
              width: 48, height: 48, borderRadius: 14, fontSize: 22,
              background: st.bg, border: `1.5px solid ${st.color}30`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              {ticket.status === 'in_progress' ? (
                <svg className="spinner" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={st.color} strokeWidth="2.5">
                  <circle cx="12" cy="12" r="10" strokeOpacity="0.2"/>
                  <path d="M12 2a10 10 0 0 1 10 10"/>
                </svg>
              ) : st.icon}
            </div>
            <div>
              <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.35)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 3 }}>Status</div>
              <div style={{ fontSize: 16, fontWeight: 700, color: st.color }}>{st.label}</div>
            </div>
          </div>

          {/* Ticket ID */}
          <div style={{
            fontFamily: 'monospace', fontSize: 15, fontWeight: 800, letterSpacing: 2,
            color: '#a78bfa', background: 'rgba(108,99,255,0.1)',
            border: '1.5px solid rgba(108,99,255,0.3)', borderRadius: 10,
            padding: '6px 16px',
          }}>
            {ticket.ticket_id}
          </div>
        </div>

        {ticket.status === 'in_progress' && (
          <div style={{
            marginTop: 20, padding: '12px 16px', borderRadius: 12,
            background: 'rgba(251,191,36,0.06)', border: '1px solid rgba(251,191,36,0.15)',
            fontSize: 13, color: 'rgba(255,255,255,0.5)',
            display: 'flex', alignItems: 'center', gap: 10,
          }}>
            <span style={{ fontSize: 16 }}>🤖</span>
            Nova is reading your message and crafting a response… This page will update automatically.
          </div>
        )}
      </div>

      {/* Details grid */}
      <div className="glass rounded-3xl" style={{ padding: '28px 32px', marginBottom: 16 }}>
        <h3 style={{ fontSize: 13, fontWeight: 700, color: 'rgba(255,255,255,0.35)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 20 }}>
          Ticket Details
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
          {[
            { label: 'Name',    value: ticket.name },
            { label: 'Email',   value: ticket.email },
            { label: 'Channel', value: `${CHANNEL_ICON[ticket.channel] || '📋'} ${ticket.channel.charAt(0).toUpperCase() + ticket.channel.slice(1)}` },
            { label: 'Created', value: new Date(ticket.created_at).toLocaleString() },
          ].map(item => (
            <div key={item.label}>
              <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.3)', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 5 }}>{item.label}</div>
              <div style={{ fontSize: 14, color: 'rgba(255,255,255,0.8)', fontWeight: 500 }}>{item.value}</div>
            </div>
          ))}
        </div>

        <div style={{ marginTop: 20, paddingTop: 20, borderTop: '1px solid rgba(255,255,255,0.06)' }}>
          <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.3)', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 8 }}>Subject</div>
          <div style={{ fontSize: 16, fontWeight: 700, color: '#fff' }}>{ticket.subject}</div>
        </div>

        <div style={{ marginTop: 16 }}>
          <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.3)', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 8 }}>Your Message</div>
          <div style={{
            fontSize: 14, color: 'rgba(255,255,255,0.55)', lineHeight: 1.7,
            background: 'rgba(255,255,255,0.03)', borderRadius: 10,
            padding: '12px 16px', border: '1px solid rgba(255,255,255,0.06)',
            whiteSpace: 'pre-wrap',
          }}>
            {ticket.description}
          </div>
        </div>
      </div>

      {/* Nova's reply */}
      {ticket.nova_response ? (
        <div className="glass rounded-3xl" style={{
          padding: '28px 32px',
          border: '1.5px solid rgba(52,211,153,0.25)',
          background: 'rgba(52,211,153,0.04)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 18 }}>
            <div style={{
              width: 36, height: 36, borderRadius: 10, fontSize: 18,
              background: 'rgba(52,211,153,0.15)', border: '1px solid rgba(52,211,153,0.3)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>🤖</div>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#34d399' }}>Nova&apos;s Response</div>
              {ticket.responded_at && (
                <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.3)' }}>
                  {new Date(ticket.responded_at).toLocaleString()}
                </div>
              )}
            </div>
            {ticket.sentiment && (
              <div style={{
                marginLeft: 'auto', fontSize: 11, fontWeight: 600,
                color: ticket.sentiment === 'positive' ? '#34d399' : ticket.sentiment === 'negative' ? '#f87171' : 'rgba(255,255,255,0.4)',
                background: 'rgba(255,255,255,0.05)', borderRadius: 8, padding: '3px 10px',
              }}>
                {ticket.sentiment === 'positive' ? '😊' : ticket.sentiment === 'negative' ? '😞' : '😐'} {ticket.sentiment}
              </div>
            )}
          </div>
          <div style={{
            fontSize: 15, color: 'rgba(255,255,255,0.75)', lineHeight: 1.8,
            whiteSpace: 'pre-wrap',
          }}>
            {ticket.nova_response}
          </div>
        </div>
      ) : (
        <div className="glass rounded-3xl" style={{ padding: '24px 32px', textAlign: 'center' }}>
          <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.3)' }}>
            ⏳ Nova&apos;s response will appear here automatically…
          </div>
        </div>
      )}

      {/* Footer actions */}
      <div style={{ marginTop: 20, display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
        <a href="/" className="nova-btn" style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 8 }}>
          ✏️ New Ticket
        </a>
        <button
          onClick={() => fetchTicket(false)}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 8,
            padding: '12px 24px', borderRadius: 12, fontSize: 14, fontWeight: 700,
            background: 'rgba(255,255,255,0.06)', border: '1.5px solid rgba(255,255,255,0.12)',
            color: 'rgba(255,255,255,0.7)', cursor: 'pointer',
          }}
        >
          🔄 Refresh
        </button>
      </div>
    </div>
  );
}
