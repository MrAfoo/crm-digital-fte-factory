'use client';

import { useState } from 'react';

type Channel = 'web' | 'email' | 'whatsapp';

interface FormData {
  fullName: string;
  email: string;
  subject: string;
  channel: Channel;
  description: string;
}

interface FormErrors {
  fullName?: string;
  email?: string;
  subject?: string;
  description?: string;
}

interface ApiError {
  message?: string;
  detail?: string;
}

const MAX_DESC = 1000;
const API_URL = 'http://localhost:8000/api/tickets';

const CHANNELS: { value: Channel; label: string; emoji: string }[] = [
  { value: 'web',       label: 'Web',       emoji: '🌐' },
  { value: 'email',     label: 'Email',     emoji: '📧' },
  { value: 'whatsapp',  label: 'WhatsApp',  emoji: '💬' },
];

export default function SupportForm() {
  const [form, setForm] = useState<FormData>({
    fullName: '', email: '', subject: '', channel: 'web', description: '',
  });
  const [errors, setErrors]       = useState<FormErrors>({});
  const [loading, setLoading]     = useState(false);
  const [ticketId, setTicketId]   = useState('');
  const [apiError, setApiError]   = useState('');
  const [charCount, setCharCount] = useState(0);

  // ── Validation ───────────────────────────────────────────
  const validate = (): boolean => {
    const e: FormErrors = {};
    if (!form.fullName.trim() || form.fullName.trim().length < 2)
      e.fullName = 'Full name must be at least 2 characters';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim()))
      e.email = 'Please enter a valid email address';
    if (!form.subject.trim() || form.subject.trim().length < 3)
      e.subject = 'Subject must be at least 3 characters';
    if (form.description.trim().length < 10)
      e.description = 'Description must be at least 10 characters';
    else if (form.description.length > MAX_DESC)
      e.description = `Max ${MAX_DESC} characters`;
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const clearError = (field: keyof FormErrors) =>
    setErrors(prev => ({ ...prev, [field]: undefined }));

  // ── Handlers ─────────────────────────────────────────────
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
    clearError(name as keyof FormErrors);
    if (name === 'description') setCharCount(value.length);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    setApiError('');
    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: form.fullName,
          email: form.email,
          subject: form.subject,
          channel: form.channel,
          description: form.description,
        }),
      });
      if (!res.ok) {
        const err: ApiError = await res.json().catch(() => ({}));
        throw new Error(err.detail || err.message || `Error ${res.status}`);
      }
      const data = await res.json();
      const tid = data.ticket_id || data.ticketId || data.id;
      if (tid) { setTicketId(tid); }
      else throw new Error(data.detail || 'Could not create ticket');
    } catch (err) {
      setApiError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setForm({ fullName: '', email: '', subject: '', channel: 'web', description: '' });
    setErrors({}); setTicketId(''); setApiError(''); setCharCount(0);
  };

  // ── Success state ─────────────────────────────────────────
  if (ticketId) return (
    <div className="glass rounded-2xl p-8 md:p-12 animate-slide-up text-center">
      <div style={{
        width: 72, height: 72, borderRadius: '50%', margin: '0 auto 20px',
        background: 'linear-gradient(135deg, #6C63FF, #f43f5e)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 32,
      }}>✅</div>
      <h2 style={{ fontSize: 28, fontWeight: 800, color: '#fff', marginBottom: 8 }}>
        You&apos;re all set!
      </h2>
      <p style={{ color: 'rgba(255,255,255,0.5)', marginBottom: 8, fontSize: 14 }}>
        Nova has received your request. Your ticket number is:
      </p>
      <div className="ticket-badge">{ticketId}</div>
      <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: 13, marginBottom: 28 }}>
        We&apos;ll reply via {form.channel} shortly. Avg response &lt; 2 min.
      </p>
      <button className="nova-btn" onClick={handleReset}>
        Submit Another Ticket
      </button>
    </div>
  );

  // ── Error state ───────────────────────────────────────────
  if (apiError) return (
    <div className="glass rounded-2xl p-8 md:p-12 animate-slide-up text-center">
      <div style={{
        width: 72, height: 72, borderRadius: '50%', margin: '0 auto 20px',
        background: 'rgba(244,63,94,0.15)', border: '2px solid rgba(244,63,94,0.3)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 32,
      }}>❌</div>
      <h2 style={{ fontSize: 24, fontWeight: 700, color: '#fff', marginBottom: 8 }}>
        Something went wrong
      </h2>
      <p style={{ color: 'rgba(255,255,255,0.5)', marginBottom: 28, fontSize: 14 }}>
        {apiError}
      </p>
      <div style={{ display: 'flex', gap: 12 }}>
        <button className="nova-btn" onClick={() => setApiError('')}>Try Again</button>
        <button className="nova-btn" style={{ background: 'rgba(255,255,255,0.08)' }} onClick={handleReset}>Reset</button>
      </div>
    </div>
  );

  // ── Form state ────────────────────────────────────────────
  return (
    <form onSubmit={handleSubmit} className="glass rounded-2xl p-8 md:p-10 animate-slide-up" noValidate>

      {/* Name + Email row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}
           className="sm-stack">
        <div>
          <label className="nova-label">Full Name <span style={{ color: '#f43f5e' }}>*</span></label>
          <input
            name="fullName" type="text" value={form.fullName}
            onChange={handleChange} placeholder="Jane Smith"
            className={`nova-input ${errors.fullName ? 'error' : ''}`}
            disabled={loading}
          />
          {errors.fullName && <div className="nova-error">⚠ {errors.fullName}</div>}
        </div>
        <div>
          <label className="nova-label">Email <span style={{ color: '#f43f5e' }}>*</span></label>
          <input
            name="email" type="email" value={form.email}
            onChange={handleChange} placeholder="you@company.com"
            className={`nova-input ${errors.email ? 'error' : ''}`}
            disabled={loading}
          />
          {errors.email && <div className="nova-error">⚠ {errors.email}</div>}
        </div>
      </div>

      {/* Subject */}
      <div style={{ marginBottom: 20 }}>
        <label className="nova-label">Subject <span style={{ color: '#f43f5e' }}>*</span></label>
        <input
          name="subject" type="text" value={form.subject}
          onChange={handleChange} placeholder="e.g., Cannot connect Gmail integration"
          className={`nova-input ${errors.subject ? 'error' : ''}`}
          disabled={loading}
        />
        {errors.subject && <div className="nova-error">⚠ {errors.subject}</div>}
      </div>

      {/* Channel */}
      <div style={{ marginBottom: 20 }}>
        <label className="nova-label">Preferred Channel <span style={{ color: '#f43f5e' }}>*</span></label>
        <div style={{ display: 'flex', gap: 12 }}>
          {CHANNELS.map(ch => (
            <button
              key={ch.value} type="button"
              className={`channel-card ${form.channel === ch.value ? 'selected' : ''}`}
              onClick={() => setForm(prev => ({ ...prev, channel: ch.value }))}
              disabled={loading}
            >
              <span style={{ fontSize: 24 }}>{ch.emoji}</span>
              {ch.label}
            </button>
          ))}
        </div>
      </div>

      {/* Description */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <label className="nova-label" style={{ marginBottom: 0 }}>
            Issue Description <span style={{ color: '#f43f5e' }}>*</span>
          </label>
          <span style={{ fontSize: 11, color: charCount > MAX_DESC * 0.9 ? '#f43f5e' : 'rgba(255,255,255,0.3)' }}>
            {charCount}/{MAX_DESC}
          </span>
        </div>
        <textarea
          name="description" value={form.description}
          onChange={handleChange} rows={5}
          placeholder="Please describe your issue in detail so Nova can help faster..."
          className={`nova-input ${errors.description ? 'error' : ''}`}
          style={{ resize: 'none' }}
          disabled={loading}
        />
        {errors.description && <div className="nova-error">⚠ {errors.description}</div>}
      </div>

      {/* Submit */}
      <button type="submit" className="nova-btn" disabled={loading}>
        {loading ? (
          <>
            <svg className="spinner" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <circle cx="12" cy="12" r="10" strokeOpacity="0.25"/>
              <path d="M12 2a10 10 0 0 1 10 10" strokeOpacity="0.75"/>
            </svg>
            Sending to Nova…
          </>
        ) : (
          <>🚀 Submit Support Ticket</>
        )}
      </button>
    </form>
  );
}
