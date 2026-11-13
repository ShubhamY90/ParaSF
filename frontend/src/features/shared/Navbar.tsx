import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/");
  }

  return (
    <nav className="bg-navy-800 border-b border-navy-700 px-6 py-3 flex items-center justify-between">
      <Link to="/" className="flex items-center gap-2">
        <span className="text-brand-green font-bold text-xl tracking-tight">Para</span>
        <span className="text-white font-bold text-xl">Trust</span>
      </Link>
      <div className="flex items-center gap-4 text-sm">
        {user ? (
          <>
            <span className="text-gray-400">
              {user.full_name ?? user.email}
              <span className="ml-2 px-2 py-0.5 rounded-full bg-brand-blue/20 text-brand-blue text-xs uppercase tracking-wide">
                {user.role}
              </span>
            </span>
            <button
              onClick={handleLogout}
              className="px-4 py-1.5 rounded-lg bg-navy-700 hover:bg-navy-600 text-white transition"
            >
              Logout
            </button>
          </>
        ) : (
          <>
            <Link to="/login" className="text-gray-300 hover:text-white transition">Login</Link>
            <Link
              to="/register"
              className="px-4 py-1.5 rounded-lg bg-brand-green text-navy font-semibold hover:bg-green-400 transition"
            >
              Register
            </Link>
          </>
        )}
      </div>
    </nav>
  );
}
