import { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom'
import './index.css'
import Login from './pages/Login'
import Collections from './pages/Collections'
import Search from './pages/Search'
import InsertVectors from './pages/InsertVectors'
import Snapshots from './pages/Snapshots'
import Security from './pages/Security'
import Nav from './components/Nav'

function isAuthed(){ return !!localStorage.getItem('qv_token') }

function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const [authed, setAuthed] = useState(isAuthed())
  const location = useLocation()

  useEffect(()=>{
    if(!isAuthed()) setAuthed(false)
  },[])

  const handleLogout = () => {
    localStorage.removeItem('qv_token')
    localStorage.removeItem('qv_csrf')
    setAuthed(false)
  }

  if(!authed) return <Login onOk={()=>setAuthed(true)} />

  const isActive = (path: string) => location.pathname === path

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav onLogout={handleLogout} />
      <div className="max-w-6xl mx-auto">
        <div className="flex gap-2 border-b px-4">
          <Link
            to="/collections"
            className={`px-3 py-2 text-sm ${isActive('/collections')?'border-b-2 border-black font-medium':''}`}
          >
            Koleksiyonlar
          </Link>
          <Link
            to="/search"
            className={`px-3 py-2 text-sm ${isActive('/search')?'border-b-2 border-black font-medium':''}`}
          >
            Arama
          </Link>
          <Link
            to="/insert"
            className={`px-3 py-2 text-sm ${isActive('/insert')?'border-b-2 border-black font-medium':''}`}
          >
            Vektör Yükle
          </Link>
          <Link
            to="/snapshots"
            className={`px-3 py-2 text-sm ${isActive('/snapshots')?'border-b-2 border-black font-medium':''}`}
          >
            Snapshots
          </Link>
          <Link
            to="/security"
            className={`px-3 py-2 text-sm ${isActive('/security')?'border-b-2 border-black font-medium':''}`}
          >
            Güvenlik
          </Link>
        </div>
        {children}
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/collections" replace />} />
        <Route path="/collections" element={<ProtectedLayout><Collections /></ProtectedLayout>} />
        <Route path="/search" element={<ProtectedLayout><Search /></ProtectedLayout>} />
        <Route path="/insert" element={<ProtectedLayout><InsertVectors /></ProtectedLayout>} />
        <Route path="/snapshots" element={<ProtectedLayout><Snapshots /></ProtectedLayout>} />
        <Route path="/security" element={<ProtectedLayout><Security /></ProtectedLayout>} />
      </Routes>
    </BrowserRouter>
  )
}
