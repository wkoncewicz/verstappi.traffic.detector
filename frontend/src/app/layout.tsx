import "@/styles/globals.css";
import Navbar from "@/components/navbar";
import Footer from "@/components/footer";
import HlsPlayer from "@/components/HlsPlayer";
import KeycloakProvider from "@/components/kcprovider";

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
          <KeycloakProvider>{children}</KeycloakProvider>
          {/* {children} */}
        </main>
        <Footer />
      </body>
    </html>
  );
}
