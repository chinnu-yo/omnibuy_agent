import './globals.css';
import React from 'react';

export const metadata = {
  title: 'OmniBuyer Agent | Razorpay AI Buildathon 2026',
  description: 'Autonomous Category-Agnostic Buyer Agent with Live Web Discovery, Deterministic Guardrails & Razorpay Checkout',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <head>
        <script src="https://checkout.razorpay.com/v1/checkout.js" async />
      </head>
      <body className="bg-zinc-950 text-zinc-100 min-h-screen flex flex-col antialiased" suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
