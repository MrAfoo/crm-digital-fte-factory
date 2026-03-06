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
    <div ref={successRef} className="glass rounded-3xl" style={{ opacity: 0, padding: '48px 40px', textAlign: 'center' }}>
      {/* Animated check ring */}
      <div className="success-icon" style={{
        width: 96, height: 96, borderRadius: '50%', margin: '0 auto 32px',
        background: 'linear-gradient(135deg, rgba(108,99,255,0.3), rgba(16,185,129,0.3))',
        border: '2px solid rgba(108,99,255,0.5)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 42,
        boxShadow: '0 0 60px rgba(108,99,255,0.35), 0 0 120px rgba(108,99,255,0.1)',
        position: 'relative',
      }}>
        ✅
        {/* Glow ring pulse — handled by CSS */}
      </div>

      <h2 style={{ fontSize: 32, fontWeight: 900, color: '#fff', marginBottom: 10, letterSpacing: '-0.5px' }}>
        You&apos;re all set!
      </h2>
      <p style={{ color: 'rgba(255,255,255,0.45)', marginBottom: 28, fontSize: 15, lineHeight: 1.6 }}>
        Nova has received your message and is processing it now.
      </p>

      {/* Ticket ID pill */}
      <div style={{
        display: 'inline-flex', alignItems: 'center', gap: 10,
        background: 'rgba(108,99,255,0.12)',
        border: '1.5px solid rgba(108,99,255,0.4)',
        borderRadius: 100, padding: '10px 24px', marginBottom: 12,
      }}>
        <span style={{ fontSize: 11, fontWeight: 600, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: 1 }}>Ticket</span>
        <span style={{ fontSize: 18, fontWeight: 800, color: '#a78bfa', fontFamily: 'monospace', letterSpacing: 2 }}>{ticketId}</span>
      </div>

      {/* Channel + ETA info */}
      <div style={{
        display: 'flex', justifyContent: 'center', gap: 24, marginBottom: 36, marginTop: 16, flexWrap: 'wrap',
      }}>
        {[
          { icon: form.channel === 'email' ? '📧' : form.channel === 'whatsapp' ? '💬' : '🌐', label: 'Reply via', value: form.channel.charAt(0).toUpperCase() + form.channel.slice(1) },
          { icon: '⚡', label: 'Response time', value: '< 2 minutes' },
          { icon: '🔒', label: 'Status', value: 'Secure & Encrypted' },
        ].map((item, i) => (
          <div key={i} style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 22, marginBottom: 4 }}>{item.icon}</div>
            <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.3)', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 2 }}>{item.label}</div>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'rgba(255,255,255,0.7)' }}>{item.value}</div>
          </div>
        ))}
      </div>

      {/* Divider */}
      <div style={{ height: 1, background: 'rgba(255,255,255,0.06)', margin: '0 0 28px' }} />

      {/* Actions */}
      <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
        {form.channel === 'whatsapp' ? (
          // WhatsApp channel — show deep link to open WhatsApp with pre-filled message
          <a
            href={`https://wa.me/15551458166?text=${encodeURIComponent(`Hi, I need help with: ${form.subject}`)}`}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 10,
              padding: '14px 32px', borderRadius: 12, fontSize: 15, fontWeight: 700,
              background: 'linear-gradient(135deg, #25D366, #128C7E)',
              color: '#fff', textDecoration: 'none',
              boxShadow: '0 4px 20px rgba(37,211,102,0.35)',
              transition: 'all 0.2s ease',
            }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
            </svg>
            Message us on WhatsApp
          </a>
        ) : (
          // Web/Email — show ticket tracker
          <a
            href={`/ticket/${ticketId}`}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              padding: '12px 28px', borderRadius: 12, fontSize: 14, fontWeight: 700,
              background: 'linear-gradient(135deg, #6C63FF, #a78bfa)',
              color: '#fff', textDecoration: 'none',
              boxShadow: '0 4px 20px rgba(108,99,255,0.4)',
              transition: 'all 0.2s ease',
            }}
          >
            📍 Track My Ticket
          </a>
        )}
        <button
          onClick={handleReset}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 8,
            padding: '12px 28px', borderRadius: 12, fontSize: 14, fontWeight: 700,
            background: 'rgba(255,255,255,0.06)',
            border: '1.5px solid rgba(255,255,255,0.12)',
            color: 'rgba(255,255,255,0.7)', cursor: 'pointer',
            transition: 'all 0.2s ease',
          }}
        >
          ✏️ Submit Another
        </button>
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
