import SupportForm from '@/components/SupportForm';

export default function Home() {
  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-nova-primary to-nova-accent bg-clip-text text-transparent">
            NovaDeskAI Support
          </h1>
          <p className="text-gray-400 text-lg">
            Submit your support request and we&apos;ll get back to you shortly
          </p>
        </div>
        <SupportForm />
      </div>
    </div>
  );
}
