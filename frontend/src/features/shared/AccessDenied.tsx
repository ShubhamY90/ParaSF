import { Link } from "react-router-dom";
export default function AccessDenied() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] gap-4">
      <div className="text-6xl">🚫</div>
      <h1 className="text-2xl font-bold text-white">Access Denied</h1>
      <p className="text-gray-400">You don't have permission to view this page.</p>
      <Link to="/" className="mt-2 px-6 py-2 bg-brand-blue text-white rounded-lg hover:bg-blue-500 transition">
        Go Home
      </Link>
    </div>
  );
}
