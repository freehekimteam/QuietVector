import { useEffect, useState } from 'react'
import './index.css'
import Login from './pages/Login'
import Collections from './pages/Collections'
import Search from './pages/Search'
import InsertVectors from './pages/InsertVectors'
import Snapshots from './pages/Snapshots'
import Security from './pages/Security'
import Nav from './components/Nav'

function isAuthed(){ return !!localStorage.getItem('qv_token') }

export default function App() {
  const [authed, setAuthed] = useState(isAuthed())
  const [tab, setTab] = useState<'collections'|'search'|'insert'|'snapshots'|'security'>('collections')

  useEffect(()=>{
    if(!isAuthed()) setAuthed(false)
  },[])

  if(!authed) return <Login onOk={()=>setAuthed(true)} />

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav onLogout={()=>{ localStorage.removeItem('qv_token'); setAuthed(false) }} />
      <div className="max-w-6xl mx-auto">
        <div className="flex gap-2 border-b px-4">
          <button className={`px-3 py-2 text-sm ${tab==='collections'?'border-b-2 border-black':''}`} onClick={()=>setTab('collections')}>Koleksiyonlar</button>
          <button className={`px-3 py-2 text-sm ${tab==='search'?'border-b-2 border-black':''}`} onClick={()=>setTab('search')}>Arama</button>
          <button className={`px-3 py-2 text-sm ${tab==='insert'?'border-b-2 border-black':''}`} onClick={()=>setTab('insert')}>Vektör Yükle</button>
          <button className={`px-3 py-2 text-sm ${tab==='snapshots'?'border-b-2 border-black':''}`} onClick={()=>setTab('snapshots')}>Snapshots</button>
          <button className={`px-3 py-2 text-sm ${tab==='security'?'border-b-2 border-black':''}`} onClick={()=>setTab('security')}>Güvenlik</button>
        </div>
        {tab==='collections' && <Collections />}
        {tab==='search' && <Search />}
        {tab==='insert' && <InsertVectors />}
        {tab==='snapshots' && <Snapshots />}
        {tab==='security' && <Security />}
      </div>
    </div>
  )
}
