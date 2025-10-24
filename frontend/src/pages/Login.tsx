import { useState } from 'react'
import { login } from '../lib/api'

export default function Login({ onOk }: { onOk: () => void }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setErr(''); setLoading(true)
    try {
      const res = await login(username.trim(), password)
      localStorage.setItem('qv_token', res.access_token)
      onOk()
    } catch (e: any) {
      setErr(e?.message || 'Giriş başarısız')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <form onSubmit={submit} className="bg-white shadow rounded p-6 w-[360px]">
        <h1 className="text-lg font-semibold mb-4">Giriş</h1>
        {err && <div className="text-sm text-red-600 mb-2">{err}</div>}
        <div className="mb-3">
          <label className="block text-sm mb-1">Kullanıcı Adı</label>
          <input className="w-full border rounded px-3 py-2" value={username} onChange={e=>setUsername(e.target.value)} required />
        </div>
        <div className="mb-3">
          <label className="block text-sm mb-1">Parola</label>
          <input type="password" className="w-full border rounded px-3 py-2" value={password} onChange={e=>setPassword(e.target.value)} required />
        </div>
        <button disabled={loading} className="w-full bg-black text-white rounded py-2 mt-2 disabled:opacity-50">{loading? 'Giriş...' : 'Giriş Yap'}</button>
      </form>
    </div>
  )
}
