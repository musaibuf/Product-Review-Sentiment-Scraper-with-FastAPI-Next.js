import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata = {
  title: 'Product Review Scraper',
  description: 'Scrape, analyze, and visualize product review sentiment.',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      {/* <body className={inter.className}>{children}</body> */}
      <body>{children}</body>
    </html>
  )
}