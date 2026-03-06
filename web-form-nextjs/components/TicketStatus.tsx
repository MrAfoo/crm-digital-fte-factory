'use client';

import { useState, useEffect, useRef } from 'react';
import { gsap } from 'gsap';

interface Ticket {
  id: string;
  status: 'open' | 'in_progress' | 'resolved' | 'escalated';
  subject: string;
  created_at: string;
  channel: string;
  response?: string;
}

interface TicketStatusProps {
  ticketId: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL
  ? `${process.env.NEXT_PUBLIC_API_URL}/api/tickets`
  : 'http://localhost:8000/api/tickets';

const getStatusColor = (status: string): { bg: string; text: string; label: string } => {
  switch (status) {
    case 'open':
      return { bg: 'rgba(59, 130, 246, 0.15)', text: '#3b82f6', label: 'Open' };
    case 'in_progress':
      return { bg: 'rgba(234, 179, 8, 0.15)', text: '#eab308', label: 'In Progress' };
    case 'resolved':
      return { bg: 'rgba(16, 185, 129, 0.15)', text: '#10b981', label: 'Resolved' };
    case 'escalated':
      return { bg: 'rgba(244, 63, 94, 0.15)', text: '#f43f5e', label: 'Escalated' };
    default:
      return { bg: 'rgba(255, 255, 255, 0.08)', text: 'rgba(255,255,255,0.6)', label: status };
  }
};

const formatDate = (dateStr: string): string => {
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateStr;
  }
};

export default function TicketStatus({ ticketId }: TicketStatusProps) {
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const cardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchTicket = async () => {
      try {
        setLoading(true);
        const res = await fetch(`${API_URL}/${ticketId}`);
        if (!res.ok) {
          throw new Error('Ticket not found');
        }
        const data = await res.json();
        setTicket(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load ticket');
      } finally {
        setLoading(false);
      }
    };

    if (ticketId) {
      fetchTicket();
    }
  }, [ticketId]);

  // GSAP entrance animation
  useEffect(() => {
    if (!loading && cardRef.current) {
      gsap.fromTo(
        cardRef.current,
        { opacity: 0, y: 30 },
        { opacity: 1, y: 0, duration: 0.6, ease: 'power3.out' }
      );
    }
  }, [loading]);

  // Loading state
  if (loading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: 300,
      }}>
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 16,
        }}>
          <div
            className="spinner"
            style={{
              width: 48,
              height: 48,
              borderRadius: '50%',
              border: '3px solid rgba(255,255,255,0.1)',
              borderTopColor: '#6C63FF',
            }}
          />
          <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: 14 }}>
            Loading ticket details...
          </p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div ref={cardRef} className="glass rounded-3xl p-10 text-center" style={{ opacity: 0 }}>
        <div style={{
          width: 80,
          height: 80,
          borderRadius: '50%',
          margin: '0 auto 24px',
          background: 'rgba(244,63,94,0.12)',
          border: '2px solid rgba(244,63,94,0.35)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 36,
        }}>
          ⚠️
        </div>
        <h2 style={{
          fontSize: 24,
          fontWeight: 700,
          color: '#fff',
          marginBottom: 8,
        }}>
          Ticket Not Found
        </h2>
        <p style={{
          color: 'rgba(255,255,255,0.5)',
          marginBottom: 28,
          fontSize: 14,
          maxWidth: 320,
          margin: '0 auto 28px',
        }}>
          {error}
        </p>
        <a
          href="/"
          className="nova-btn"
          style={{ textDecoration: 'none', display: 'inline-flex' }}
        >
          ← Back to Support
        </a>
      </div>
    );
  }

  if (!ticket) {
    return null;
  }

  const statusColor = getStatusColor(ticket.status);

  return (
    <div ref={cardRef} className="glass rounded-3xl p-8 md:p-10" style={{ opacity: 0 }}>
      {/* Header with status badge */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: 24,
        gap: 16,
        flexWrap: 'wrap',
      }}>
        <div>
          <p style={{
            fontSize: 11,
            fontWeight: 600,
            color: 'rgba(255,255,255,0.4)',
            textTransform: 'uppercase',
            letterSpacing: 0.8,
            marginBottom: 6,
          }}>
            Ticket ID
          </p>
          <p style={{
            fontSize: 28,
            fontWeight: 800,
            color: '#fff',
            fontFamily: "'Courier New', monospace",
            letterSpacing: 2,
          }}>
            {ticket.id}
          </p>
        </div>
        <div
          style={{
            background: statusColor.bg,
            border: `1.5px solid ${statusColor.text}`,
            color: statusColor.text,
            padding: '8px 16px',
            borderRadius: 12,
            fontSize: 13,
            fontWeight: 700,
            letterSpacing: 0.3,
          }}
        >
          {statusColor.label}
        </div>
      </div>

      {/* Details Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: 24,
        marginBottom: 28,
      }} className="sm-stack">
        {/* Subject */}
        <div>
          <p style={{
            fontSize: 11,
            fontWeight: 600,
            color: 'rgba(255,255,255,0.4)',
            textTransform: 'uppercase',
            letterSpacing: 0.8,
            marginBottom: 8,
          }}>
            Subject
          </p>
          <p style={{
            fontSize: 14,
            color: 'rgba(255,255,255,0.9)',
            lineHeight: 1.5,
          }}>
            {ticket.subject}
          </p>
        </div>

        {/* Channel */}
        <div>
          <p style={{
            fontSize: 11,
            fontWeight: 600,
            color: 'rgba(255,255,255,0.4)',
            textTransform: 'uppercase',
            letterSpacing: 0.8,
            marginBottom: 8,
          }}>
            Communication Channel
          </p>
          <p style={{
            fontSize: 14,
            color: 'rgba(255,255,255,0.9)',
          }}>
            {ticket.channel.charAt(0).toUpperCase() + ticket.channel.slice(1)}
          </p>
        </div>

        {/* Created At */}
        <div>
          <p style={{
            fontSize: 11,
            fontWeight: 600,
            color: 'rgba(255,255,255,0.4)',
            textTransform: 'uppercase',
            letterSpacing: 0.8,
            marginBottom: 8,
          }}>
            Created At
          </p>
          <p style={{
            fontSize: 14,
            color: 'rgba(255,255,255,0.9)',
          }}>
            {formatDate(ticket.created_at)}
          </p>
        </div>
      </div>

      {/* Response Section */}
      {ticket.response && (
        <div style={{
          background: 'rgba(108, 99, 255, 0.08)',
          border: '1.5px solid rgba(108, 99, 255, 0.25)',
          borderRadius: 16,
          padding: 20,
          marginBottom: 24,
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            marginBottom: 12,
          }}>
            <span style={{ fontSize: 18 }}>🤖</span>
            <p style={{
              fontSize: 12,
              fontWeight: 700,
              color: '#a78bfa',
              textTransform: 'uppercase',
              letterSpacing: 0.5,
            }}>
              Nova AI Response
            </p>
          </div>
          <p style={{
            fontSize: 14,
            color: 'rgba(255,255,255,0.85)',
            lineHeight: 1.6,
          }}>
            {ticket.response}
          </p>
        </div>
      )}

      {/* Action Buttons */}
      <div style={{
        display: 'flex',
        gap: 12,
        flexDirection: 'column',
        marginTop: 28,
      }}>
        <a
          href="/"
          className="nova-btn"
          style={{
            textDecoration: 'none',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          ← Submit Another Ticket
        </a>
        <button
          className="nova-btn"
          style={{
            background: 'rgba(255,255,255,0.07)',
            border: '1px solid rgba(255,255,255,0.1)',
          }}
          onClick={() => window.location.reload()}
        >
          🔄 Refresh Status
        </button>
      </div>
    </div>
  );
}
