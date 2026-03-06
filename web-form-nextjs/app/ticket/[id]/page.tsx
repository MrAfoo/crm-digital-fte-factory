import TicketStatus from '@/components/TicketStatus';
import Link from 'next/link';

interface TicketPageProps {
  params: {
    id: string;
  };
}

export async function generateMetadata({ params }: TicketPageProps) {
  return {
    title: `Ticket ${params.id} - NovaDeskAI Support`,
    description: `Check the status of support ticket ${params.id}`,
  };
}

export default function TicketPage({ params }: TicketPageProps) {
  const ticketId = decodeURIComponent(params.id).toUpperCase();

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="mb-8">
          <Link
            href="/"
            className="inline-flex items-center text-nova-primary hover:text-nova-accent transition-colors mb-6"
          >
            <svg
              className="w-5 h-5 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
            Back to Support Form
          </Link>
          <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-nova-primary to-nova-accent bg-clip-text text-transparent">
            Ticket Status
          </h1>
          <p className="text-gray-400 text-lg">
            Track your support request in real-time
          </p>
        </div>

        {/* Ticket Status Component */}
        <TicketStatus ticketId={ticketId} />
      </div>
    </div>
  );
}
