'use client';

import { useState } from 'react';

// Type definitions
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

// Constants
const MAX_DESCRIPTION_LENGTH = 1000;
const API_ENDPOINT = 'http://localhost:8000/api/tickets';

export default function SupportForm() {
  // State management
  const [formData, setFormData] = useState<FormData>({
    fullName: '',
    email: '',
    subject: '',
    channel: 'web',
    description: '',
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [ticketId, setTicketId] = useState<string>('');
  const [submitError, setSubmitError] = useState<string>('');
  const [charCount, setCharCount] = useState(0);

  // Validation functions
  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.fullName.trim()) {
      newErrors.fullName = 'Full name is required';
    } else if (formData.fullName.trim().length < 2) {
      newErrors.fullName = 'Full name must be at least 2 characters';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!validateEmail(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (!formData.subject.trim()) {
      newErrors.subject = 'Subject is required';
    } else if (formData.subject.trim().length < 3) {
      newErrors.subject = 'Subject must be at least 3 characters';
    }

    if (!formData.description.trim()) {
      newErrors.description = 'Description is required';
    } else if (formData.description.trim().length < 10) {
      newErrors.description = 'Description must be at least 10 characters';
    } else if (formData.description.length > MAX_DESCRIPTION_LENGTH) {
      newErrors.description = `Description cannot exceed ${MAX_DESCRIPTION_LENGTH} characters`;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Event handlers
  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));

    // Clear error for this field when user starts typing
    if (errors[name as keyof FormErrors]) {
      setErrors((prev) => ({
        ...prev,
        [name]: undefined,
      }));
    }
  };

  const handleChannelChange = (channel: Channel) => {
    setFormData((prev) => ({
      ...prev,
      channel,
    }));
  };

  const handleDescriptionChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const { value } = e.target;
    setFormData((prev) => ({
      ...prev,
      description: value,
    }));
    setCharCount(value.length);

    // Clear error when user starts typing
    if (errors.description) {
      setErrors((prev) => ({
        ...prev,
        description: undefined,
      }));
    }
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    setSubmitError('');

    try {
      const response = await fetch(API_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData: ApiError = await response.json().catch(() => ({
          message: 'Failed to submit form',
        }));
        throw new Error(errorData.detail || errorData.message || 'Failed to submit form');
      }

      const data = await response.json();

      // API returns { ticket_id, estimated_response_time, ... }
      const tid = data.ticket_id || data.ticketId || data.id;
      if (tid) {
        setTicketId(tid);
        setIsSubmitted(true);
      } else {
        throw new Error(data.detail || data.message || 'Failed to create support ticket');
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'An unexpected error occurred';
      setSubmitError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetry = () => {
    setSubmitError('');
    setIsLoading(false);
  };

  const handleReset = () => {
    setFormData({
      fullName: '',
      email: '',
      subject: '',
      channel: 'web',
      description: '',
    });
    setErrors({});
    setIsSubmitted(false);
    setTicketId('');
    setSubmitError('');
    setCharCount(0);
  };

  // Success state
  if (isSubmitted && ticketId) {
    return (
      <div className="glass rounded-2xl p-8 md:p-12 animate-slide-up">
        <div className="text-center">
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 bg-gradient-to-br from-nova-primary to-nova-accent rounded-full flex items-center justify-center">
              <svg
                className="w-8 h-8 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
          </div>
          <h2 className="text-3xl font-bold mb-4 text-white">Success!</h2>
          <p className="text-gray-300 mb-6">
            Your support ticket has been created successfully.
          </p>
          <div className="bg-nova-dark bg-opacity-50 rounded-lg p-6 mb-8 border border-nova-primary border-opacity-30">
            <p className="text-sm text-gray-400 mb-2">Your Ticket ID</p>
            <p className="text-2xl font-mono font-bold text-nova-primary">{ticketId}</p>
            <p className="text-xs text-gray-400 mt-3">
              Keep this ID for your records. You can use it to check your ticket status.
            </p>
          </div>
          <p className="text-gray-400 mb-6">
            We&apos;ll review your request and get back to you shortly via {formData.channel}.
          </p>
          <button
            onClick={handleReset}
            className="w-full bg-gradient-to-r from-nova-primary to-nova-accent hover:shadow-lg hover:shadow-nova-primary/50 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-300 transform hover:scale-105"
          >
            Submit Another Ticket
          </button>
        </div>
      </div>
    );
  }

  // Error state
  if (submitError) {
    return (
      <div className="glass rounded-2xl p-8 md:p-12 animate-slide-up">
        <div className="text-center">
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 bg-nova-accent bg-opacity-20 rounded-full flex items-center justify-center">
              <svg
                className="w-8 h-8 text-nova-accent"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4m0 4v.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
          </div>
          <h2 className="text-2xl font-bold mb-4 text-white">Something went wrong</h2>
          <p className="text-gray-300 mb-8">{submitError}</p>
          <div className="flex gap-4">
            <button
              onClick={handleRetry}
              className="flex-1 bg-gradient-to-r from-nova-primary to-nova-accent hover:shadow-lg hover:shadow-nova-primary/50 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-300"
            >
              Try Again
            </button>
            <button
              onClick={handleReset}
              className="flex-1 border border-nova-primary text-nova-primary hover:bg-nova-primary hover:bg-opacity-10 font-semibold py-3 px-6 rounded-lg transition-all duration-300"
            >
              Reset Form
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Form state
  return (
    <form onSubmit={handleSubmit} className="glass rounded-2xl p-8 md:p-12 animate-slide-up">
      {/* Full Name Field */}
      <div className="mb-6">
        <label htmlFor="fullName" className="block text-sm font-semibold text-white mb-2">
          Full Name <span className="text-nova-accent">*</span>
        </label>
        <input
          type="text"
          id="fullName"
          name="fullName"
          value={formData.fullName}
          onChange={handleInputChange}
          placeholder="John Doe"
          className={`w-full px-4 py-3 rounded-lg bg-nova-dark bg-opacity-50 border-2 ${
            errors.fullName ? 'border-nova-accent' : 'border-nova-primary border-opacity-30'
          } text-white placeholder-gray-500 focus:border-nova-primary focus:bg-opacity-70 focus:shadow-lg focus:shadow-nova-primary/20`}
          disabled={isLoading}
        />
        {errors.fullName && (
          <p className="text-nova-accent text-xs mt-2 animate-slide-up">{errors.fullName}</p>
        )}
      </div>

      {/* Email Field */}
      <div className="mb-6">
        <label htmlFor="email" className="block text-sm font-semibold text-white mb-2">
          Email Address <span className="text-nova-accent">*</span>
        </label>
        <input
          type="email"
          id="email"
          name="email"
          value={formData.email}
          onChange={handleInputChange}
          placeholder="john@example.com"
          className={`w-full px-4 py-3 rounded-lg bg-nova-dark bg-opacity-50 border-2 ${
            errors.email ? 'border-nova-accent' : 'border-nova-primary border-opacity-30'
          } text-white placeholder-gray-500 focus:border-nova-primary focus:bg-opacity-70 focus:shadow-lg focus:shadow-nova-primary/20`}
          disabled={isLoading}
        />
        {errors.email && (
          <p className="text-nova-accent text-xs mt-2 animate-slide-up">{errors.email}</p>
        )}
      </div>

      {/* Subject Field */}
      <div className="mb-6">
        <label htmlFor="subject" className="block text-sm font-semibold text-white mb-2">
          Subject <span className="text-nova-accent">*</span>
        </label>
        <input
          type="text"
          id="subject"
          name="subject"
          value={formData.subject}
          onChange={handleInputChange}
          placeholder="e.g., Cannot login to my account"
          className={`w-full px-4 py-3 rounded-lg bg-nova-dark bg-opacity-50 border-2 ${
            errors.subject ? 'border-nova-accent' : 'border-nova-primary border-opacity-30'
          } text-white placeholder-gray-500 focus:border-nova-primary focus:bg-opacity-70 focus:shadow-lg focus:shadow-nova-primary/20`}
          disabled={isLoading}
        />
        {errors.subject && (
          <p className="text-nova-accent text-xs mt-2 animate-slide-up">{errors.subject}</p>
        )}
      </div>

      {/* Channel Selection */}
      <div className="mb-6">
        <label className="block text-sm font-semibold text-white mb-4">
          Preferred Contact Channel <span className="text-nova-accent">*</span>
        </label>
        <div className="flex flex-col sm:flex-row gap-4">
          {(['web', 'email', 'whatsapp'] as const).map((ch) => (
            <label
              key={ch}
              className="flex items-center cursor-pointer group"
            >
              <input
                type="radio"
                name="channel"
                value={ch}
                checked={formData.channel === ch}
                onChange={() => handleChannelChange(ch)}
                disabled={isLoading}
                className="w-4 h-4 cursor-pointer"
              />
              <span className="ml-3 text-gray-300 group-hover:text-nova-primary transition-colors">
                {ch.charAt(0).toUpperCase() + ch.slice(1)}
              </span>
            </label>
          ))}
        </div>
      </div>

      {/* Description Field */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <label htmlFor="description" className="block text-sm font-semibold text-white">
            Issue Description <span className="text-nova-accent">*</span>
          </label>
          <span
            className={`text-xs ${
              charCount > MAX_DESCRIPTION_LENGTH * 0.9
                ? 'text-nova-accent'
                : 'text-gray-400'
            }`}
          >
            {charCount}/{MAX_DESCRIPTION_LENGTH}
          </span>
        </div>
        <textarea
          id="description"
          name="description"
          value={formData.description}
          onChange={handleDescriptionChange}
          placeholder="Please describe your issue in detail..."
          rows={5}
          maxLength={MAX_DESCRIPTION_LENGTH}
          className={`w-full px-4 py-3 rounded-lg bg-nova-dark bg-opacity-50 border-2 ${
            errors.description ? 'border-nova-accent' : 'border-nova-primary border-opacity-30'
          } text-white placeholder-gray-500 focus:border-nova-primary focus:bg-opacity-70 focus:shadow-lg focus:shadow-nova-primary/20 resize-none`}
          disabled={isLoading}
        />
        {errors.description && (
          <p className="text-nova-accent text-xs mt-2 animate-slide-up">{errors.description}</p>
        )}
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isLoading}
        className="w-full bg-gradient-to-r from-nova-primary to-nova-accent hover:shadow-lg hover:shadow-nova-primary/50 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 px-6 rounded-lg transition-all duration-300 transform hover:scale-105 disabled:hover:scale-100 flex items-center justify-center gap-2"
      >
        {isLoading ? (
          <>
            <svg className="w-5 h-5 spinner" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            Submitting...
          </>
        ) : (
          <>
            Submit Support Ticket
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 7l5 5m0 0l-5 5m5-5H6"
              />
            </svg>
          </>
        )}
      </button>
    </form>
  );
}
