import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/providers/theme-provider";
import ReduxProvider from "@/components/providers/redux-provider";
import { Toaster } from "sonner";
import { Nav } from "@/components/section/header/nav";
import { ModalProvider } from "@/components/providers/modal-provider";

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
      <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
      <main className="min-h-screen flex flex-col">
         <Nav />
        {children}
      </main>
        <ModalProvider />
        <Toaster position={"bottom-left"} closeButton/>
      </ThemeProvider>
      </ReduxProvider>
      </body>
    </html>
  );
}
