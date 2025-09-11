'use client'
export default function LogoutLink() {
  const onClick = (e: React.MouseEvent) => {
    e.preventDefault()
    localStorage.removeItem('token')
    location.href = '/login'
  }
  return (
    <a href="/login" onClick={onClick} className="text-sm opacity-70 hover:opacity-100 transition">
      Выйти
    </a>
  )
}