import React from 'react';
import './globals.css';

export const metadata = {
  title: 'Chatbot Project',
  description: 'A chatbot application using Next.js and FastAPI',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  );
}