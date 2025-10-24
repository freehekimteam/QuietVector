import { useState } from 'react'

async function prepare(newKey: string, adminPassword: string) {
  const r = await fetch('/api/security/qdrant_key/prepare', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ new_key: newKey, admin_password: adminPassword })
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json() as Promise<{ op_id: string; apply_instructions: string[] }>
}

export default function Security() {
  const [key1, setKey1] = useState('')
  const [key2, setKey2] = useState('')
  const [pwd, setPwd] = useState('')
  const [msg, setMsg] = useState('')
  const [err, setErr] = useState('')
  const [opId, setOpId] = useState('')
  const [instr, setInstr] = useState<string[]>([])
  const [loading, setLoading] = useState(false)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setMsg(''); setErr(''); setOpId(''); setInstr([]); setLoading(true)
    try {
      if (key1 !== key2) throw new Error('Anahtarlar eşleşmiyor')
      const res = await prepare(key1, pwd)
      setOpId(res.op_id)
      setInstr(res.apply_instructions)
      setMsg('Yeni anahtar kaydedildi. Uygulamak için talimatları izleyin.')
      setKey1(''); setKey2(''); setPwd('')
    } catch (e:any) {
      setErr(e?.message || 'İşlem hatası')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold">Güvenlik</h2>
      <form onSubmit={submit} className="mt-4 border rounded p-3 max-w-xl">
        <h3 className="font-medium mb-2">Qdrant API Anahtarı Döndürme (Hazırlık)</h3>
        <div className="text-sm text-gray-600 mb-2">Yeni anahtarı yalnızca yetkili kullanıcılar görebilir. Uygulama, anahtarı sunucu tarafında güvenli dosyaya yazar (0600). Qdrant'ı yeniden başlattıktan sonra aktif olur.</div>
        <div className="grid gap-2">
          <input className="border rounded px-3 py-2" placeholder="Yeni Anahtar" value={key1} onChange={e=>setKey1(e.target.value)} required />
          <input className="border rounded px-3 py-2" placeholder="Yeni Anahtar (tekrar)" value={key2} onChange={e=>setKey2(e.target.value)} required />
          <input type="password" className="border rounded px-3 py-2" placeholder="Admin Parola" value={pwd} onChange={e=>setPwd(e.target.value)} required />
          <button disabled={loading} className="bg-black text-white rounded px-3 py-2 w-48 disabled:opacity-50">{loading? 'Kaydediliyor...' : 'Hazırla'}</button>
        </div>
      </form>

      {msg && <div className="text-sm text-green-700 mt-3">{msg}</div>}
      {err && <div className="text-sm text-red-600 mt-3">{err}</div>}
      {opId && (
        <div className="mt-4 border rounded p-3 max-w-2xl bg-gray-50">
          <div className="text-sm">İşlem ID: <b>{opId}</b></div>
          <div className="text-sm mt-2">Uygulama Talimatları:</div>
          <pre className="text-xs whitespace-pre-wrap mt-2">{instr.join('\n')}</pre>
        </div>
      )}
    </div>
  )
}

