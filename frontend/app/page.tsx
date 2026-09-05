'use client';

import dynamic from 'next/dynamic';

const OmniBuyerApp = dynamic(() => import('../components/OmniBuyerApp'), {
  ssr: false,
  loading: () => (
    <div className="flex flex-col h-screen bg-zinc-950 text-zinc-100 font-sans items-center justify-center">
      <div className="flex items-center gap-3 bg-zinc-900 border border-zinc-800 px-6 py-4 rounded-2xl shadow-xl">
        <div className="h-3 w-3 rounded-full bg-emerald-400 animate-ping" />
        <span className="text-xs font-semibold tracking-wider text-zinc-300 font-mono">Initializing OmniBuyer Agent...</span>
      </div>
    </div>
  ),
});

export default function Page() {
  return <OmniBuyerApp />;
}
