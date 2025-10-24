import logo from '../assets/logo.svg';

export default function Nav({ onLogout }: { onLogout: () => void }) {
  return (
    <div className="flex items-center justify-between border-b border-gray-200 p-3">
      <div className="flex items-center gap-2">
        <img src={logo} alt="QuietVector" className="w-7 h-7" />
        <span className="font-semibold">QuietVector</span>
      </div>
      <button onClick={onLogout} className="text-sm text-gray-600 hover:text-black">Çıkış</button>
    </div>
  );
}
