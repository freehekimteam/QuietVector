import { useEffect, useState } from 'react'
import './index.css'
import Login from './pages/Login'
import Collections from './pages/Collections'
import Search from './pages/Search'
import Nav from './components/Nav'

function isAuthed(){ return !!localStorage.getItem('qv_token') }

export default function App() {
  const [authed, setAuthed] = useState(isAuthed())
  const [tab, setTab] = useState<'collections'|'search'>('collections')

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
        </div>
        {tab==='collections' && <Collections />}
        {tab==='search' && <Search />}
      </div>
    </div>
  )
}
