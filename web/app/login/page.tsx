'use client'
import { useState } from 'react'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async () => {
    setError('')
    setLoading(true)
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/admin/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      if (!res.ok) throw new Error('Неверные данные')
      const data = await res.json()
      localStorage.setItem('token', data.access_token)
      location.href = '/admin'
    } catch (e: any) {
      setError(e?.message?.replace(/["{}]/g, '') || 'Ошибка входа')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="grid place-items-center min-h-[70vh] px-4">
      <div className="group relative w-full max-w-md">
        {/* мягкое свечение вокруг карточки */}
        <div
          aria-hidden
          className="absolute -inset-0.5 rounded-3xl bg-gradient-to-tr from-sky-400/35 via-fuchsia-500/35 to-violet-600/35 opacity-40 blur-md transition group-hover:opacity-60"
        />
        {/* ТЁМНАЯ СТЕКЛЯННАЯ КАРТОЧКА */}
        <div className="relative rounded-3xl bg-neutral-950/60 backdrop-blur-xl border border-white/10 shadow-2xl p-7 text-neutral-100">
          <div className="mb-5 flex items-center gap-2">
            <div className="h-8 w-8 rounded-xl bg-gradient-to-tr from-sky-400 via-fuchsia-500 to-violet-600" />
            <h1 className="text-xl font-semibold tracking-tight">Вход в админ-панель</h1>
          </div>

          <label className="text-xs uppercase tracking-wide text-white/60">Email</label>
          <input
            className="mt-1 w-full rounded-xl bg-white/5 text-white placeholder:text-white/40
                       ring-1 ring-white/10 focus:ring-2 focus:ring-violet-400/40
                       px-3 py-2 shadow-inner"
            placeholder="you@example.com"
            type="email"
            value={email}
            onChange={(e)=>setEmail(e.target.value)}
            autoComplete="email"
          />

          <label className="mt-4 text-xs uppercase tracking-wide text-white/60 block">Пароль</label>
          <input
            className="mt-1 w-full rounded-xl bg-white/5 text-white placeholder:text-white/40
                       ring-1 ring-white/10 focus:ring-2 focus:ring-violet-400/40
                       px-3 py-2 shadow-inner"
            placeholder="••••••••"
            type="password"
            value={password}
            onChange={(e)=>setPassword(e.target.value)}
            autoComplete="current-password"
          />

          {error && <p className="mt-3 text-sm text-rose-400">{error}</p>}

          <button
            onClick={submit}
            disabled={loading || !email || !password}
            className="mt-6 w-full rounded-xl bg-gradient-to-r from-violet-600 to-sky-500
                       text-white py-2.5 font-medium shadow
                       hover:shadow-lg active:translate-y-px transition
                       disabled:opacity-50"
          >
            {loading ? 'Входим…' : 'Войти'}
          </button>

          <p className="mt-3 text-xs text-white/50">Демо: используйте учётку из .env</p>
        </div>
      </div>
    </div>
  )
}