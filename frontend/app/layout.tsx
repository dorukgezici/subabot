import Footer from "@/components/Footer";
import "@fortawesome/fontawesome-svg-core/styles.css";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import { Inter } from "next/font/google";
import type { ReactNode } from "react";
import "./globals.scss";

dayjs.extend(relativeTime);

export const metadata = {
  title: "Subabot",
  description:
    "An AI-powered Slack alert bot to subscribe, classify and notify for keywords on the web.",
};

const font = Inter({ subsets: ["latin"] });

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className={font.className}>
        {children}
        <Footer />
      </body>
    </html>
  );
}
