'use client'
import { useEffect, useMemo, useRef, useState } from 'react'

type Task = { id:number; title:string; order:number; status:'pending'|'in_progress'|'done' }
type Project = { id:number; title:string; description:string; tasks:Task[] }
type User = { id:number; tg_id:string; name:string; email:string; projects:Project[] }

const API = process.env.NEXT_PUBLIC_API_BASE_URL!

/* ========== UI bits ========== */
function ProgressBar({ value }: { value: number }) {
  const v = Math.min(100, Math.max(0, value))
  return (
    <div className="h-2.5 rounded-full bg-black/5 dark:bg-white/10 overflow-hidden">
      <div
        className="h-full rounded-full bg-gradient-to-r from-sky-400 via-fuchsia-500 to-violet-600 transition-[width] duration-300 ease-out"
        style={{ width: `${v}%` }}
      />
    </div>
  )
}
function StatusBadge({ s }: { s: Task['status'] }) {
  const map = {
    pending: 'bg-blue-100 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300',
    in_progress: 'bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300',
    done: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300',
  }
  return <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${map[s]}`}>{s}</span>
}

/* ========== Admin Page ========== */
type ReviewState = {
  running: boolean
  value: number
  comment?: string
  error?: string
}

export default function AdminPage(){
  const [users, setUsers] = useState<User[]>([])
  const [query, setQuery] = useState('')
  const [token, setToken] = useState<string>('')
  const [ready, setReady] = useState(false)  

  const [review, setReview] = useState<Record<number, ReviewState>>({})
  const controllersRef = useRef<Map<number, AbortController>>(new Map())
  const animTimersRef = useRef<Map<number, boolean>>(new Map())

  useEffect(() => {
    const t = localStorage.getItem('token')
    if (!t) {
      location.href = '/login'
      return
    }
    setToken(t)
    setReady(true)
  }, [])

  const fetchUsers = async () => {
    if (!token) return
    const res = await fetch(`${API}/admin/users`, { headers: { Authorization: `Bearer ${token}` } })
    if (res.ok) {
      const data = await res.json()
      setUsers(data.users)
    }
  }
  useEffect(() => { if (ready) fetchUsers() }, [ready, token])

  const setStatus = async (taskId:number, status:Task['status']) => {
    await fetch(`${API}/admin/tasks/${taskId}?status=${status}`, {
      method:'PATCH',
      headers: { Authorization: `Bearer ${token}` }
    })
    fetchUsers()
  }

  /* ===== AI Review с «живым» прогрессом ===== */
  const startAnimatedProgress = (projectId: number) => {
    animTimersRef.current.set(projectId, true)
    const tick = () => {
      if (!animTimersRef.current.get(projectId)) return
      setReview(prev => {
        const cur = prev[projectId] || { running:true, value:0 }
        const next = Math.min(92, cur.value + Math.max(1, Math.floor(Math.random()*3)))
        return { ...prev, [projectId]: { ...cur, running: true, value: next } }
      })
      setTimeout(tick, 350 + Math.floor(Math.random()*120))
    }
    tick()
  }
  const stopAnimatedProgress = (projectId: number) => {
    animTimersRef.current.set(projectId, false)
  }

  const reviewProject = async (projectId:number) => {
    if (review[projectId]?.running) return

    setReview(prev => ({ ...prev, [projectId]: { running: true, value: 0, comment: undefined, error: undefined } }))
    startAnimatedProgress(projectId)

    const ctrl = new AbortController()
    controllersRef.current.set(projectId, ctrl)

    try {
      const res = await fetch(`${API}/ai/review/${projectId}`, { method:'POST', signal: ctrl.signal })
      const data = await res.json().catch(()=>({ percent: 0, comment: 'Нет данных' }))
      const percent = Math.max(0, Math.min(100, Number(data.percent ?? 0)))
      const comment = String(data.comment ?? '')

      // останавливаем анимацию, докручиваем до реального процента
      stopAnimatedProgress(projectId)
      setReview(prev => ({ ...prev, [projectId]: { running: true, value: Math.max(prev[projectId]?.value ?? 0, percent) } }))
      // маленькая «склейка» (на глаз) и финиш
      setTimeout(() => {
        setReview(prev => ({ ...prev, [projectId]: { running: false, value: percent, comment } }))
      }, 500)

    } catch (e:any) {
      stopAnimatedProgress(projectId)
      setReview(prev => ({ ...prev, [projectId]: { running: false, value: 0, error: e?.message || 'Ошибка запроса' } }))
    } finally {
      controllersRef.current.delete(projectId)
    }
  }

  const cancelReview = (projectId:number) => {
    const ctrl = controllersRef.current.get(projectId)
    if (ctrl) {
      ctrl.abort()
      controllersRef.current.delete(projectId)
    }
    stopAnimatedProgress(projectId)
    setReview(prev => ({ ...prev, [projectId]: { running: false, value: 0, comment: undefined, error: 'Отменено' } }))
  }

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return users
    return users
      .map(u => ({
        ...u,
        projects: u.projects.filter(p =>
          p.title.toLowerCase().includes(q) ||
          p.description.toLowerCase().includes(q) ||
          u.name.toLowerCase().includes(q) ||
          u.email.toLowerCase().includes(q)
        )
      }))
      .filter(u => u.projects.length > 0)
  }, [users, query])

  if (!ready) return null

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-2xl font-semibold">Пользователи и проекты</h1>
        <div className="flex items-center gap-2">
          <input
            className="w-72 max-w-full rounded-xl border border-black/10 dark:border-white/10 bg-white/70 dark:bg-neutral-900 px-3 py-2 shadow-inner"
            placeholder="Поиск: имя, email, проект…"
            value={query}
            onChange={e=>setQuery(e.target.value)}
          />
          <a
            href="/login"
            onClick={(e)=>{ e.preventDefault(); localStorage.removeItem('token'); location.href='/login' }}
            className="rounded-xl border border-black/10 dark:border-white/10 px-3 py-2 text-sm hover:bg-black/5 dark:hover:bg-white/10 transition"
          >
            Выйти
          </a>
        </div>
      </div>

      <div className="space-y-6">
        {filtered.map(u=> (
          <section key={u.id} className="rounded-3xl border border-black/5 dark:border-white/10 bg-white/70 dark:bg-neutral-900/60 backdrop-blur shadow-xl p-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="font-semibold">{u.name}</div>
                <div className="text-sm opacity-70">{u.email} · tg:{u.tg_id}</div>
              </div>
            </div>

            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              {u.projects.map(p=> {
                const total = p.tasks.length || 1
                const done = p.tasks.filter(t=>t.status==='done').length
                const percent = Math.round((done/total)*100)

                const r = review[p.id]
                const isRunning = r?.running
                const barValue = isRunning ? r.value : (r?.value ?? percent)
                const hasResult = !!r?.comment && !isRunning
                const hasError = !!r?.error && !isRunning

                return (
                  <article key={p.id} className="rounded-2xl border border-black/5 dark:border-white/10 bg-white/70 dark:bg-neutral-900/60 p-4 shadow">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="font-medium">{p.title}</div>
                        <p className="text-sm opacity-70 line-clamp-3">{p.description}</p>
                      </div>

                      {/* AI Review actions */}
                      <div className="flex items-center gap-2">
                        {!isRunning && (
                          <button
                            onClick={()=>reviewProject(p.id)}
                            className="rounded-lg bg-gray-900 text-white text-sm px-3 py-1.5 shadow hover:shadow-md active:scale-[.98] transition"
                            title="AI Review"
                          >
                            🤖 AI Review
                          </button>
                        )}
                        {isRunning && (
                          <button
                            onClick={()=>cancelReview(p.id)}
                            className="rounded-lg border border-black/10 dark:border-white/10 text-sm px-3 py-1.5 hover:bg-black/5 dark:hover:bg-white/10 transition"
                            title="Отменить"
                          >
                            Отменить
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Progress (общий по задачам) */}
                    <div className="mt-3">
                      <div className="flex items-center justify-between text-xs mb-1 opacity-70">
                        <span>Прогресс задач</span><span>{percent}%</span>
                      </div>
                      <ProgressBar value={percent} />
                    </div>

                    {/* AI Review live progress */}
                    <div className="mt-3">
                      <div className="flex items-center justify-between text-xs mb-1 opacity-70">
                        <span>{isRunning ? 'Анализируем идею' : 'Последний AI-отзыв'}</span>
                        <span>{barValue}%</span>
                      </div>
                      <ProgressBar value={barValue} />
                      {isRunning && (
                        <div className="mt-2 text-xs opacity-70">Генерация инсайтов… это займёт чуть-чуть времени.</div>
                      )}
                      {hasResult && (
                        <div className="mt-2 rounded-xl border border-black/5 dark:border-white/10 bg-black/[0.03] dark:bg-white/5 p-3 text-sm">
                          {r!.comment}
                        </div>
                      )}
                      {hasError && (
                        <div className="mt-2 rounded-xl border border-red-200/60 dark:border-red-500/30 bg-red-50/80 dark:bg-red-500/10 text-red-700 dark:text-red-300 p-3 text-sm">
                          {r!.error}
                        </div>
                      )}
                    </div>

                    {/* Tasks */}
                    <div className="mt-3 divide-y divide-black/5 dark:divide-white/10">
                      {p.tasks.sort((a,b)=>a.order-b.order).map(t=> (
                        <div key={t.id} className="py-2 flex items-center justify-between gap-3">
                          <div className="text-sm"><span className="opacity-50">{t.order+1}.</span> {t.title}</div>
                          <div className="flex items-center gap-2">
                            <StatusBadge s={t.status} />
                            <div className="hidden sm:flex gap-1">
                              <button onClick={()=>setStatus(t.id,'pending')} className="rounded-lg px-2 py-1 text-xs border border-black/10 dark:border-white/10 hover:bg-black/5 dark:hover:bg-white/10">pending</button>
                              <button onClick={()=>setStatus(t.id,'in_progress')} className="rounded-lg px-2 py-1 text-xs border border-black/10 dark:border-white/10 hover:bg-black/5 dark:hover:bg-white/10">in_progress</button>
                              <button onClick={()=>setStatus(t.id,'done')} className="rounded-lg px-2 py-1 text-xs border border-black/10 dark:border-white/10 hover:bg-black/5 dark:hover:bg-white/10">done</button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </article>
                )
              })}
            </div>
          </section>
        ))}
        {filtered.length === 0 && (
          <div className="rounded-3xl border border-black/5 dark:border-white/10 bg-white/70 dark:bg-neutral-900/60 p-10 text-center">
            <div className="mx-auto h-10 w-10 rounded-2xl bg-gradient-to-tr from-sky-400 via-fuchsia-500 to-violet-600 mb-3" />
            <div className="font-medium">Ничего не найдено</div>
            <div className="text-sm opacity-70">Попробуйте изменить запрос в поиске</div>
          </div>
        )}
      </div>
    </div>
  )
}