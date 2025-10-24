import { useState } from 'react'
import { createSnapshot, listSnapshots, restoreSnapshot } from '../lib/api'

type SnapItem = { name: string; creation_time?: string; size?: number }

export default function Snapshots() {
  const [collection, setCollection] = useState('')
  const [items, setItems] = useState<SnapItem[]>([])
  const [file, setFile] = useState<File|undefined>(undefined)
  const [msg, setMsg] = useState('')
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)

  async function load() {
    setMsg(''); setErr('')
    try {
      const res = await listSnapshots(collection)
      setItems(res?.result || res?.snapshots || [])
    } catch (e:any) {
      setErr(e?.message || 'Listeleme hatası')
    }
  }

  async function create() {
    setMsg(''); setErr(''); setLoading(true)
    try {
      await createSnapshot(collection)
      setMsg('Snapshot oluşturma başlatıldı')
      await load()
    } catch (e:any) {
      setErr(e?.message || 'Oluşturma hatası')
    } finally {
      setLoading(false)
    }
  }

  async function restore(e: React.FormEvent) {
    e.preventDefault()
    if (!file) { setErr('Dosya seçin'); return }
    setMsg(''); setErr(''); setLoading(true)
    try {
      await restoreSnapshot(collection, file)
      setMsg('Geri yükleme başlatıldı')
    } catch (e:any) {
      setErr(e?.message || 'Geri yükleme hatası')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold">Snapshots</h2>
      {msg && <div className="text-sm text-green-600 mt-2">{msg}</div>}
      {err && <div className="text-sm text-red-600 mt-2">{err}</div>}
      <div className="mt-3 flex gap-2 items-center">
        <input className="border rounded px-3 py-2" placeholder="Koleksiyon" value={collection} onChange={e=>setCollection(e.target.value)} />
        <button onClick={load} className="border rounded px-3 py-2">Listele</button>
        <button disabled={!collection || loading} onClick={create} className="bg-black text-white rounded px-3 py-2 disabled:opacity-50">Oluştur</button>
      </div>

      <div className="mt-4">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left border-b">
              <th className="py-2">Ad</th>
              <th>Boyut</th>
              <th>Oluşturma</th>
            </tr>
          </thead>
          <tbody>
            {items.map((x:any)=> (
              <tr key={x.name} className="border-b">
                <td className="py-2">{x.name}</td>
                <td>{x.size || '-'}</td>
                <td>{x.creation_time || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <form onSubmit={restore} className="mt-6 border rounded p-3 max-w-xl">
        <h3 className="font-medium mb-2">Restore</h3>
        <div className="text-sm text-gray-600 mb-2">Qdrant'a snapshot yükleyerek koleksiyonu geri yükleyin.</div>
        <input type="file" onChange={e=>setFile(e.target.files?.[0])} />
        <div className="mt-2">
          <button disabled={!collection || !file || loading} className="bg-black text-white rounded px-3 py-2 disabled:opacity-50">Yükle</button>
        </div>
      </form>
    </div>
  )
}

