import { Bricolage_Grotesque, JetBrains_Mono } from "next/font/google";
import { Features } from "./_components/features";
import { Footer } from "./_components/footer";
import { Hero } from "./_components/hero";
import { Steps } from "./_components/steps";
import { Ticker } from "./_components/ticker";

const display = Bricolage_Grotesque({
  subsets: ["latin"],
  variable: "--font-sy-display",
});

const syMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-sy-mono",
});

export default function HomePage() {
  return (
    <div className={`${display.variable} ${syMono.variable}`}>
      <Hero />
      <Ticker />
      <Features />
      <Steps />
      <Footer />
    </div>
  );
}
