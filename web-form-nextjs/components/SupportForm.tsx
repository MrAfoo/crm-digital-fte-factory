'use client';

import { useState, useEffect, useRef } from 'react';
import { gsap } from 'gsap';

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
const API_URL = process.env.NEXT_PUBLIC_API_URL
  ? `${process.env.NEXT_PUBLIC_API_URL}/api/tickets`
  : 'http://localhost:8000/api/tickets';

const CHANNELS: { value: Channel; label: string; icon: string; desc: string }[] = [
  { value: 'web',      label: 'Web Chat',  icon: '🌐', desc: 'Reply in browser' },
  { value: 'email',    label: 'Email',     icon: '📧', desc: 'Reply via email'  },
  { value: 'whatsapp', label: 'WhatsApp',  icon: '💬', desc: 'Reply on WhatsApp'},
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

  const formRef    = useRef<HTMLFormElement>(null);
  const successRef = useRef<HTMLDivElement>(null);
  const errorRef   = useRef<HTMLDivElement>(null);
  const fieldsRef  = useRef<HTMLDivElement[]>([]);
  const btnRef     = useRef<HTMLButtonElement>(null);

  // Entrance animation
  useEffect(() => {
    if (!formRef.current) return;
    const fields = fieldsRef.current.filter(Boolean);
    gsap.set(fields, { opacity: 0, y: 30 });
    gsap.to(fields, {
      opacity: 1, y: 0,
      duration: 0.5,
      stagger: 0.08,
      ease: 'power3.out',
      delay: 0.1,
    });
  }, []);

  // Success animation
  useEffect(() => {
    if (!ticketId || !successRef.current) return;
    gsap.fromTo(successRef.current,
      { opacity: 0, scale: 0.85, y: 40 },
      { opacity: 1, scale: 1, y: 0, duration: 0.6, ease: 'back.out(1.4)' }
    );
    // Bounce the check icon
    const icon = successRef.current.querySelector('.success-icon');
    if (icon) {
      gsap.fromTo(icon,
        { scale: 0, rotate: -30 },
        { scale: 1, rotate: 0, duration: 0.5, ease: 'back.out(2)', delay: 0.3 }
      );
    }
  }, [ticketId]);

  // Error animation
  useEffect(() => {
    if (!apiError || !errorRef.current) return;
    gsap.fromTo(errorRef.current,
      { opacity: 0, x: -20 },
      { opacity: 1, x: 0, duration: 0.4, ease: 'power2.out' }
    );
    // Shake effect
    gsap.to(errorRef.current, {
      x: [-8, 8, -6, 6, -4, 4, 0],
      duration: 0.4,
      ease: 'power1.inOut',
      delay: 0.1,
    });
  }, [apiError]);

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
    // Shake invalid fields
    Object.keys(e).forEach(field => {
      const el = formRef.current?.querySelector(`[name="${field}"]`);
      if (el) gsap.to(el, { x: [-6, 6, -4, 4, 0], duration: 0.3, ease: 'power1.inOut' });
    });
    return Object.keys(e).length === 0;
  };

  const clearError = (field: keyof FormErrors) =>
    setErrors(prev => ({ ...prev, [field]: undefined }));

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
    clearError(name as keyof FormErrors);
    if (name === 'description') setCharCount(value.length);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    // Button pulse animation
    if (btnRef.current) {
      gsap.to(btnRef.current, { scale: 0.96, duration: 0.1, yoyo: true, repeat: 1 });
    }

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
      if (tid) setTicketId(tid);
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

  const addFieldRef = (el: HTMLDivElement | null, index: number) => {
    if (el) fieldsRef.current[index] = el;
  };

  // ── Success state ─────────────────────────────────────────
  if (ticketId) return (
    <div ref={successRef} className="glass rounded-3xl p-10 text-center" style={{ opacity: 0 }}>
      <div className="success-icon" style={{
        width: 80, height: 80, borderRadius: '50%', margin: '0 auto 24px',
        background: 'linear-gradient(135deg, #6C63FF, #10b981)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 36,
        boxShadow: '0 0 40px rgba(108,99,255,0.4)',
      }}>✅</div>
      <h2 style={{ fontSize: 30, fontWeight: 800, color: '#fff', marginBottom: 8 }}>
        You&apos;re all set!
      </h2>
      <p style={{ color: 'rgba(255,255,255,0.5)', marginBottom: 12, fontSize: 15 }}>
        Nova has received your request. Your ticket:
      </p>
      <div className="ticket-badge">{ticketId}</div>
      <p style={{ color: 'rgba(255,255,255,0.35)', fontSize: 13, marginBottom: 32 }}>
        We&apos;ll reply via <strong style={{ color: '#a78bfa' }}>{form.channel}</strong> · Avg response &lt; 2 min
      </p>
      <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
        <button className="nova-btn" onClick={handleReset}>Submit Another</button>
        <a
          href={`/ticket/${ticketId}`}
          className="nova-btn"
          style={{ background: 'rgba(255,255,255,0.07)', textDecoration: 'none', display: 'inline-flex', alignItems: 'center' }}
        >
          Track Ticket →
        </a>
      </div>
    </div>
  );

  // ── Error state ───────────────────────────────────────────
  if (apiError) return (
    <div ref={errorRef} className="glass rounded-3xl p-10 text-center" style={{ opacity: 0 }}>
      <div style={{
        width: 80, height: 80, borderRadius: '50%', margin: '0 auto 24px',
        background: 'rgba(244,63,94,0.12)', border: '2px solid rgba(244,63,94,0.35)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 36,
      }}>⚠️</div>
      <h2 style={{ fontSize: 24, fontWeight: 700, color: '#fff', marginBottom: 8 }}>
        Something went wrong
      </h2>
      <p style={{ color: 'rgba(255,255,255,0.5)', marginBottom: 28, fontSize: 14, maxWidth: 320, margin: '0 auto 28px' }}>
        {apiError}
      </p>
      <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
        <button className="nova-btn" onClick={() => setApiError('')}>Try Again</button>
        <button className="nova-btn" style={{ background: 'rgba(255,255,255,0.07)' }} onClick={handleReset}>Reset Form</button>
      </div>
    </div>
  );

  // ── Form state ────────────────────────────────────────────
  return (
    <form ref={formRef} onSubmit={handleSubmit} className="glass rounded-3xl p-8 md:p-10" noValidate>

      {/* Name + Email */}
      <div ref={el => addFieldRef(el, 0)} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }} className="sm-stack">
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
      <div ref={el => addFieldRef(el, 1)} style={{ marginBottom: 20 }}>
        <label className="nova-label">Subject <span style={{ color: '#f43f5e' }}>*</span></label>
        <input
          name="subject" type="text" value={form.subject}
          onChange={handleChange} placeholder="e.g., Cannot connect Gmail integration"
          className={`nova-input ${errors.subject ? 'error' : ''}`}
          disabled={loading}
        />
        {errors.subject && <div className="nova-error">⚠ {errors.subject}</div>}
      </div>

      {/* Channel selector */}
      <div ref={el => addFieldRef(el, 2)} style={{ marginBottom: 20 }}>
        <label className="nova-label">Preferred Channel <span style={{ color: '#f43f5e' }}>*</span></label>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 10 }}>
          {CHANNELS.map(ch => (
            <button
              key={ch.value} type="button"
              onClick={() => {
                setForm(prev => ({ ...prev, channel: ch.value }));
                const el = document.querySelector(`[data-ch="${ch.value}"]`);
                if (el) gsap.to(el, { scale: [1.08, 1], duration: 0.25, ease: 'back.out(2)' });
              }}
              data-ch={ch.value}
              disabled={loading}
              style={{
                display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4,
                padding: '14px 8px', borderRadius: 14, cursor: 'pointer',
                border: form.channel === ch.value
                  ? '2px solid rgba(108,99,255,0.8)'
                  : '2px solid rgba(255,255,255,0.08)',
                background: form.channel === ch.value
                  ? 'linear-gradient(135deg, rgba(108,99,255,0.2), rgba(167,139,250,0.1))'
                  : 'rgba(255,255,255,0.04)',
                transition: 'all 0.2s ease',
                boxShadow: form.channel === ch.value ? '0 0 20px rgba(108,99,255,0.25)' : 'none',
              }}
            >
              <span style={{ fontSize: 22 }}>{ch.icon}</span>
              <span style={{ fontSize: 12, fontWeight: 700, color: form.channel === ch.value ? '#a78bfa' : 'rgba(255,255,255,0.6)' }}>{ch.label}</span>
              <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.3)' }}>{ch.desc}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Description */}
      <div ref={el => addFieldRef(el, 3)} style={{ marginBottom: 28 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <label className="nova-label" style={{ marginBottom: 0 }}>
            Issue Description <span style={{ color: '#f43f5e' }}>*</span>
          </label>
          <span style={{
            fontSize: 11, fontVariantNumeric: 'tabular-nums',
            color: charCount > MAX_DESC * 0.9 ? '#f43f5e' : 'rgba(255,255,255,0.25)',
            transition: 'color 0.3s',
          }}>
            {charCount}/{MAX_DESC}
          </span>
        </div>
        <textarea
          name="description" value={form.description}
          onChange={handleChange} rows={5}
          placeholder="Describe your issue in detail so Nova can help faster…"
          className={`nova-input ${errors.description ? 'error' : ''}`}
          style={{ resize: 'none' }}
          disabled={loading}
        />
        {errors.description && <div className="nova-error">⚠ {errors.description}</div>}
      </div>

      {/* Submit */}
      <div ref={el => addFieldRef(el, 4)}>
        <button ref={btnRef} type="submit" className="nova-btn" disabled={loading} style={{ width: '100%', fontSize: 15 }}>
          {loading ? (
            <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10 }}>
              <svg className="spinner" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <circle cx="12" cy="12" r="10" strokeOpacity="0.25"/>
                <path d="M12 2a10 10 0 0 1 10 10" strokeOpacity="0.85"/>
              </svg>
              Sending to Nova…
            </span>
          ) : (
            <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
              🚀 Submit Support Ticket
            </span>
          )}
        </button>

        <p style={{ textAlign: 'center', marginTop: 14, fontSize: 11, color: 'rgba(255,255,255,0.2)' }}>
          🔒 Encrypted · Nova AI replies in &lt;2 min · No spam
        </p>
      </div>
    </form>
  );
}
