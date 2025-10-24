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

  function validate(points: Point[]): string[] {
    const errors: string[] = []
    if (!Array.isArray(points) || points.length === 0) {
      errors.push('Boş liste')
      return errors
    }
    // Vector boyutu tutarlılığı
    const dim = Array.isArray(points[0].vector) ? points[0].vector.length : 0
    points.forEach((p, idx) => {
      if (typeof p.id !== 'string' && typeof p.id !== 'number') errors.push(`#${idx}: id tipi geçersiz`)
      if (!Array.isArray(p.vector) || p.vector.length === 0) errors.push(`#${idx}: vector geçersiz`)
      if (Array.isArray(p.vector) && p.vector.some(v => typeof v !== 'number' || Number.isNaN(v))) errors.push(`#${idx}: vector sayısal olmalı`)
      if (Array.isArray(p.vector) && p.vector.length !== dim) errors.push(`#${idx}: vector boyutu tutarsız (beklenen ${dim})`)
      if (p.payload && typeof p.payload !== 'object') errors.push(`#${idx}: payload obje olmalı`)
    })
    return errors
  }

  function example() {
    setJsonText('[\n  {"id": 1, "vector": [0.1, 0.2, 0.3], "payload": {"title": "Örnek"}},\n  {"id": "doc-2", "vector": [0.4, 0.5, 0.6], "payload": {"tags": ["a","b"]}}\n]')
  }

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
      const errors = validate(points)
      if (errors.length) throw new Error('Doğrulama hatası:\n' + errors.join('\n'))
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
        <div className="flex gap-2 items-center">
          <button type="button" onClick={example} className="border rounded px-3 py-2">Örnek Doldur</button>
          <button disabled={loading} className="bg-black text-white rounded px-3 py-2 w-40 disabled:opacity-50">{loading? 'Yükleniyor...' : 'Yükle'}</button>
        </div>
      </form>
    </div>
  )
}
