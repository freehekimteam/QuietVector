import { useEffect, useState } from 'react'
import { createCollection, listCollections } from '../lib/api'

export default function Collections() {
  const [items, setItems] = useState<any[]>([])
  const [name, setName] = useState('')
  const [size, setSize] = useState(1536)
  const [distance, setDistance] = useState<'Cosine'|'Dot'|'Euclid'>('Cosine')
  const [err, setErr] = useState('')

  async function load() {
    try {
      setErr('')
      const data = await listCollections()
      setItems(data)
    } catch (e:any) {
      setErr(e?.message || 'Hata')
    }
  }

  useEffect(()=>{ load() },[])

  async function create(e: React.FormEvent) {
    e.preventDefault()
    try {
      await createCollection({ name, vectors_size: size, distance })
      setName('');
      await load()
    } catch (e:any) {
      setErr(e?.message || 'Oluşturma hatası')
    }
  }

  return (
    <div className="p-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Koleksiyonlar</h2>
        <button className="text-sm text-gray-600" onClick={load}>Yenile</button>
      </div>
      {err && <div className="text-sm text-red-600 mt-2">{err}</div>}

      <div className="mt-4">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left border-b">
              <th className="py-2">Ad</th>
              <th>Points</th>
              <th>Vectors</th>
              <th>Durum</th>
            </tr>
          </thead>
          <tbody>
            {items.map((x:any)=> (
              <tr key={x.name} className="border-b">
                <td className="py-2">{x.name}</td>
                <td>{x.points_count}</td>
                <td>{x.vectors_count}</td>
                <td>{x.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <form onSubmit={create} className="mt-6 border rounded p-3 max-w-xl">
        <h3 className="font-medium mb-2">Yeni Koleksiyon</h3>
        <div className="grid grid-cols-3 gap-3">
          <input className="border rounded px-3 py-2" placeholder="Ad" value={name} onChange={e=>setName(e.target.value)} required />
          <input type="number" className="border rounded px-3 py-2" placeholder="Vektor Boyutu" value={size} onChange={e=>setSize(parseInt(e.target.value||'0',10))} required />
          <select className="border rounded px-3 py-2" value={distance} onChange={e=>setDistance(e.target.value as any)}>
            <option>Cosine</option>
            <option>Dot</option>
            <option>Euclid</option>
          </select>
        </div>
        <button className="bg-black text-white rounded px-3 py-2 mt-3">Oluştur</button>
      </form>
    </div>
  )
}
