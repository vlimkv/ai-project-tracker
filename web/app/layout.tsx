import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import LogoutLink from '../components/LogoutLink'

const inter = Inter({ subsets: ['latin', 'cyrillic'] })

export const metadata: Metadata = {
  title: 'Admin | AI Project Tracker',
  description: 'Админ-панель и инструменты для AI Project Tracker',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" suppressHydrationWarning>
      <body className={`${inter.className} min-h-screen bg-gray-50 text-gray-900 dark:bg-neutral-950 dark:text-neutral-100`}>
        <div className="pointer-events-none fixed inset-0 -z-10 bg-grid" />
        <header className="sticky top-0 z-20 border-b border-black/5 dark:border-white/10 backdrop-blur bg-white/70 dark:bg-neutral-950/60">
          <div className="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="h-6 w-6 rounded-xl bg-gradient-to-tr from-sky-400 via-fuchsia-500 to-violet-600 shadow-sm" />
              <span className="font-semibold">AI Project Tracker</span>
              <span className="ml-2 rounded-full bg-black/5 px-2 py-0.5 text-xs dark:bg-white/10">admin</span>
            </div>
            <nav className="text-sm">
              <a className="opacity-70 hover:opacity-100 transition" href="/admin">Панель</a>
              <span className="mx-3 opacity-30">•</span>
              <LogoutLink />
            </nav>
          </div>
        </header>

        <main className="mx-auto max-w-6xl px-4 py-10">{children}</main>

        <footer className="mx-auto max-w-6xl px-4 py-8 text-xs opacity-60">
          © {new Date().getFullYear()} AI Project Tracker
        </footer>
      </body>
    </html>
  )
}
