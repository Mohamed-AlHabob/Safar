import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/core/providers/theme-provider";
import ReduxProvider from "@/core/providers/redux-provider";
import { Toaster } from "sonner";
import { ModalProvider } from "@/core/providers/modal-provider";
import { WebSocketProvider } from "@/core/providers/websocket-provider";
import { Nav } from "@/components/layout/header/nav";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Safar",
  description: "Safar is a travel app",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased custom-scrollbar`}
      >
      <ReduxProvider>
      <WebSocketProvider>
      <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
      <main className="min-h-screen flex flex-col">
        {children}
      </main>
        <ModalProvider />
        <Toaster position={"top-center"} closeButton/>
      </ThemeProvider>
      </WebSocketProvider>
      </ReduxProvider>
      </body>
    </html>
  );
}
