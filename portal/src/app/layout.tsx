import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Gini Voice Portal - Memphis Retro',
  description: 'Voice-RAG dashboard built on Memphis Retro design systems.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark h-full">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=block"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-full flex flex-col font-syne antialiased">
        {children}
      </body>
    </html>
  );
}
