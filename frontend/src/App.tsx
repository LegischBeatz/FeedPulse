import { NavLink, Route, Routes } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import FeedExplorer from './pages/FeedExplorer';

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <nav className="bg-blue-600 text-white px-4 py-2 flex justify-between">
        <h1 className="font-bold">FeedPulse</h1>
        <div className="space-x-4">
          <NavLink to="/" className={({isActive}) => isActive ? 'font-bold' : ''}>Dashboard</NavLink>
          <NavLink to="/explore" className={({isActive}) => isActive ? 'font-bold' : ''}>Explore</NavLink>
        </div>
      </nav>
      <main className="flex-1 p-4">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/explore" element={<FeedExplorer />} />
        </Routes>
      </main>
    </div>
  );
}
