import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";
import { Toaster } from "react-hot-toast";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "AutoRadixAI — Medical AI Platform",
  description:
    "AI-powered core radiology intelligence platform that automates medical imaging workflows.",
  icons: { icon: "/favicon.ico" },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased bg-slate-50 dark:bg-slate-950`}>
        <Providers>
          {children}
          <Toaster
            position="top-right"
            toastOptions={{
              className: "text-sm font-medium",
              duration: 4000,
            }}
          />
        </Providers>
      </body>
    </html>
  );
}
