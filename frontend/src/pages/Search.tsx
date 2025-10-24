import { useState } from 'react'
import { searchVector } from '../lib/api'

export default function Search() {
  const [collection, setCollection] = useState('')
  const [vec, setVec] = useState('')
  const [limit, setLimit] = useState(5)
  const [results, setResults] = useState<any[]>([])
  const [err, setErr] = useState('')

  async function run(e: React.FormEvent) {
    e.preventDefault()
    setErr('')
    try {
      const vector = vec.split(',').map(v=>parseFloat(v.trim())).filter(v=>!Number.isNaN(v))
      const data = await searchVector({ collection, vector, limit })
      setResults(data.results || [])
    } catch (e:any) {
      setErr(e?.message || 'Arama hatası')
    }
  }

  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold">Arama</h2>
      {err && <div className="text-sm text-red-600 mt-2">{err}</div>}
      <form onSubmit={run} className="mt-3 grid gap-3 max-w-3xl">
        <input className="border rounded px-3 py-2" placeholder="Koleksiyon" value={collection} onChange={e=>setCollection(e.target.value)} required />
        <input className="border rounded px-3 py-2" placeholder="Vektör (1,2,3,...)" value={vec} onChange={e=>setVec(e.target.value)} required />
        <input type="number" className="border rounded px-3 py-2 w-40" value={limit} onChange={e=>setLimit(parseInt(e.target.value||'0',10))} />
        <button className="bg-black text-white rounded px-3 py-2 w-40">Ara</button>
      </form>
      <div className="mt-4">
        {results.length>0 && (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left border-b">
                <th className="py-2">ID</th><th>Score</th><th>Payload</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r:any)=> (
                <tr key={r.id} className="border-b">
                  <td className="py-2">{r.id}</td>
                  <td>{r.score.toFixed(4)}</td>
                  <td><pre className="text-xs whitespace-pre-wrap">{JSON.stringify(r.payload,null,2)}</pre></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
