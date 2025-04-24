import type { Metadata } from "next";
import { Provider } from "@/components/ui/provider"
import { Toaster } from "@/components/ui/toaster"
import Header from "@/components/Header";

import "./globals.css";

export const metadata: Metadata = {
  title: "Web Events Dashboard",
  description: "Display and edit web events",
};

export default function RootLayout(props: { children: React.ReactNode }) {
  const { children } = props
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <Provider>
          <Header />
          <main>
            {children}
            <Toaster />
          </main>
        </Provider>
      </body>
    </html>
  )
}