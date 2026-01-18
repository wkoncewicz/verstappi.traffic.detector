import "@/styles/globals.css";
import Navbar from "./components/navbar";
import Footer from "./components/footer";
import HlsPlayer from "./components/HlsPlayer";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pl">
      <body className="app-shell">
        <Navbar />
        <main className="app-main">
            <div style={{ padding: 24, maxWidth:720 }}>
              <HlsPlayer src="https://wzmedia.dot.ca.gov/D3/99_JCT162E_BUT99_NB.stream/chunklist_w646513265.m3u8" />
            </div>
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}
