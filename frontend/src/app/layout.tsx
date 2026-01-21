import "@/styles/globals.css";
import Navbar from "@/components/navbar";
import Footer from "@/components/footer";
import KeycloakProvider from "@/components/kcprovider";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pl">
      <body className="app-shell">
        <KeycloakProvider>
          <Navbar />
          <main className="app-main">
            {children}
          </main>
          <Footer />
        </KeycloakProvider>
      </body>
    </html>
  );
}
