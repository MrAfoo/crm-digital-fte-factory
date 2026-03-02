'use client';

import { useState } from 'react';

// Type definitions
interface ConversationMessage {
  id: string;
  author: string;
  message: string;
  timestamp: string;
}

interface Ticket {
  id: string;
  status: string;
  subject: string;
  createdDate: string;
  lastUpdated: string;
  priority: string;
  channel: string;
  conversation: ConversationMessage[];
}

interface ApiError {
  message: string;
}

interface TicketStatusProps {
  initialTicketId?: string;
}

const STATUS_COLORS: Record<string, string> = {
  open: 'bg-nova-primary',
  in_progress: 'bg-yellow-500',
  resolved: 'bg-green-500',
  closed: 'bg-gray-500',
};

const PRIORITY_COLORS: Record<string, string> = {
  low: 'text-blue-400',
  medium: 'text-yellow-400',
  high: 'text-nova-accent',
  urgent: 'text-red-500',
};

export default function TicketStatus({ initialTicketId = '' }: TicketStatusProps) {
  const [ticketId, setTicketId] = useState<string>(initialTicketId);
  const [searchInput, setSearchInput] = useState<string>(initialTicketId);
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!searchInput.trim()) {
      setError('Please enter a ticket ID');
      return;
    }

    setIsLoading(true);
    setError('');
    setTicket(null);
    setHasSearched(true);

    try {
      const response = await fetch(
        `http://localhost:8000/api/tickets/${searchInput.trim()}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        const errorData: ApiError = await response.json().catch(() => ({
          message: 'Ticket not found',
        }));
        throw new Error(errorData.message || 'Ticket not found');
      }

      const data: Ticket = await response.json();
      setTicket(data);
      setTicketId(searchInput.trim());
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch ticket';
      setError(errorMessage);
      setTicket(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setTicketId('');
    setSearchInput('');
    setTicket(null);
    setError('');
    setHasSearched(false);
  };

  const formatDate = (dateString: string): string => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateString;
    }
  };

  return (
    <div className="w-full">
      {/* Search Form */}
      <form onSubmit={handleSearch} className="glass rounded-2xl p-8 mb-6 animate-slide-up">
        <h2 className="text-2xl font-bold text-white mb-6">Check Ticket Status</h2>
        <div className="flex flex-col sm:flex-row gap-4">
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value.toUpperCase())}
            placeholder="Enter ticket ID (e.g., TKT-12345)"
            className="flex-1 px-4 py-3 rounded-lg bg-nova-dark bg-opacity-50 border-2 border-nova-primary border-opacity-30 text-white placeholder-gray-500 focus:border-nova-primary focus:bg-opacity-70 focus:shadow-lg focus:shadow-nova-primary/20"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading}
            className="bg-gradient-to-r from-nova-primary to-nova-accent hover:shadow-lg hover:shadow-nova-primary/50 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 px-8 rounded-lg transition-all duration-300 whitespace-nowrap"
          >
            {isLoading ? (
              <svg className="w-5 h-5 spinner inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            ) : (
              'Search'
            )}
          </button>
        </div>
      </form>

      {/* Error State */}
      {error && hasSearched && (
        <div className="glass rounded-2xl p-8 mb-6 animate-slide-up border-l-4 border-nova-accent">
          <div className="flex items-start gap-4">
            <svg className="w-6 h-6 text-nova-accent flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4v.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-white mb-2">Not Found</h3>
              <p className="text-gray-300">{error}</p>
              <button
                onClick={handleReset}
                className="mt-4 text-nova-primary hover:text-nova-accent transition-colors text-sm font-medium"
              >
                Try Another Ticket ID
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Ticket Details */}
      {ticket && (
        <div className="space-y-6 animate-slide-up">
          {/* Header */}
          <div className="glass rounded-2xl p-8">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
              <div>
                <h3 className="text-3xl font-bold text-white font-mono">{ticket.id}</h3>
                <p className="text-gray-400 text-sm mt-1">{ticket.subject}</p>
              </div>
              <div className="flex items-center gap-3">
                <div className={`w-3 h-3 rounded-full ${STATUS_COLORS[ticket.status.toLowerCase()] || 'bg-gray-500'}`} />
                <span className="text-white font-semibold capitalize">{ticket.status}</span>
              </div>
            </div>

            {/* Metadata */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">Priority</p>
                <p className={`font-semibold capitalize ${PRIORITY_COLORS[ticket.priority.toLowerCase()] || 'text-gray-300'}`}>
                  {ticket.priority}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">Channel</p>
                <p className="text-gray-300 font-semibold capitalize">{ticket.channel}</p>
              </div>
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">Created</p>
                <p className="text-gray-300 font-semibold text-sm">{formatDate(ticket.createdDate)}</p>
              </div>
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">Last Updated</p>
                <p className="text-gray-300 font-semibold text-sm">{formatDate(ticket.lastUpdated)}</p>
              </div>
            </div>
          </div>

          {/* Conversation History */}
          {ticket.conversation && ticket.conversation.length > 0 && (
            <div className="glass rounded-2xl p-8">
              <h4 className="text-xl font-bold text-white mb-6">Conversation History</h4>
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {ticket.conversation.map((msg, index) => (
                  <div
                    key={msg.id || index}
                    className="bg-nova-dark bg-opacity-50 rounded-lg p-4 border border-nova-primary border-opacity-20"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <p className="font-semibold text-white">{msg.author}</p>
                      <p className="text-xs text-gray-400">{formatDate(msg.timestamp)}</p>
                    </div>
                    <p className="text-gray-300">{msg.message}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* No Conversation */}
          {(!ticket.conversation || ticket.conversation.length === 0) && (
            <div className="glass rounded-2xl p-8 text-center">
              <p className="text-gray-400">No conversation history yet. We&apos;ll update you soon.</p>
            </div>
          )}

          {/* Reset Button */}
          <button
            onClick={handleReset}
            className="w-full border border-nova-primary text-nova-primary hover:bg-nova-primary hover:bg-opacity-10 font-semibold py-3 px-6 rounded-lg transition-all duration-300"
          >
            Check Another Ticket
          </button>
        </div>
      )}

      {/* Empty State */}
      {!ticket && !error && hasSearched && (
        <div className="glass rounded-2xl p-12 text-center animate-slide-up">
          <svg className="w-12 h-12 text-gray-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <p className="text-gray-400">Loading ticket information...</p>
        </div>
      )}
    </div>
  );
}
