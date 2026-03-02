import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'NovaDeskAI - Support Form',
  description: 'Submit support tickets and track their status with NovaDeskAI',
  viewport: 'width=device-width, initial-scale=1.0',
  charset: 'utf-8',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="animated-bg">
          <div className="orb orb-primary" />
          <div className="orb orb-accent" />
          <div className="orb orb-secondary" />
        </div>
        <main className="relative z-10">
          {children}
        </main>
      </body>
    </html>
  );
}
