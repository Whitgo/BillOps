/**
 * Header Component
 */

export default function Header() {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
      <div className="flex-between">
        <h1 className="text-2xl font-bold text-gray-900">BillOps</h1>
        <div className="flex items-center gap-4">
          <button className="btn btn-sm btn-outline">Settings</button>
          <button className="btn btn-sm btn-outline">Logout</button>
        </div>
      </div>
    </header>
  );
}
