import { useState } from 'react'
import { insertVectors } from '../lib/api'

type Point = { id: string|number; vector: number[]; payload?: any }

export default function InsertVectors() {
  const [collection, setCollection] = useState('')
  const [jsonText, setJsonText] = useState('[\n  {"id": 1, "vector": [0.1, 0.2], "payload": {"k":"v"}}\n]')
  const [file, setFile] = useState<File|undefined>(undefined)
  const [msg, setMsg] = useState('')
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setMsg(''); setErr(''); setLoading(true)
    try {
      let points: Point[]
      if (file) {
        const text = await file.text()
        points = JSON.parse(text)
      } else {
        points = JSON.parse(jsonText)
      }
      if (!Array.isArray(points) || points.length === 0) throw new Error('Geçersiz points verisi')
      const res = await insertVectors({ collection, points })
      setMsg(`Yüklendi: ${res.inserted}`)
    } catch (e:any) {
      setErr(e?.message || 'Yükleme hatası')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold">Vektör Yükle</h2>
      {msg && <div className="text-sm text-green-600 mt-2">{msg}</div>}
      {err && <div className="text-sm text-red-600 mt-2">{err}</div>}
      <form onSubmit={submit} className="mt-4 grid gap-3 max-w-4xl">
        <input className="border rounded px-3 py-2" placeholder="Koleksiyon" value={collection} onChange={e=>setCollection(e.target.value)} required />
        <div className="text-sm text-gray-600">JSON ile ya da dosya seçerek yükleyebilirsiniz. Dosya seçerseniz metin gözardı edilir.</div>
        <textarea className="border rounded px-3 py-2 font-mono h-48" value={jsonText} onChange={e=>setJsonText(e.target.value)} />
        <input type="file" accept="application/json,.json" onChange={e=>setFile(e.target.files?.[0])} />
        <button disabled={loading} className="bg-black text-white rounded px-3 py-2 w-40 disabled:opacity-50">{loading? 'Yükleniyor...' : 'Yükle'}</button>
      </form>
    </div>
  )
}

