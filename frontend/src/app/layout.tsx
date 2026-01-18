import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Aura - SEO & AEO Analysis Platform',
  description: '차세대 SEO & AEO 통합 분석 플랫폼',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body>
        <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
          {/* Header */}
          <header className="bg-white shadow-sm border-b border-gray-200">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <h1 className="text-2xl font-bold text-primary-600">Aura</h1>
                  <span className="ml-3 text-sm text-gray-500">SEO & AEO Analysis</span>
                </div>
                <nav className="flex items-center gap-6">
                  <a href="/" className="text-gray-600 hover:text-primary-600 transition font-medium">
                    Single URL
                  </a>
                  <a href="/competitive" className="text-gray-600 hover:text-primary-600 transition font-medium">
                    Competitive
                  </a>
                </nav>
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>

          {/* Footer */}
          <footer className="bg-white border-t border-gray-200 mt-16">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
              <p className="text-center text-sm text-gray-500">
                © 2025 Aura. All rights reserved.
              </p>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
