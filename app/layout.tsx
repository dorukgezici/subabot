import type { ReactNode } from 'react';
import { Inter } from 'next/font/google';
import '@fortawesome/fontawesome-svg-core/styles.css';
import Footer from '@/components/Footer';
import './globals.css';

export const metadata = {
  title: 'Subabot',
  description: 'An AI-powered Slack alert bot to subscribe, classify and notify for keywords on the web.'
};

const font = Inter({ subsets: ['latin'] });


export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang='en'>
    <body className={font.className}>
    {children}
    <Footer />
    </body>
    </html>
  );
}
