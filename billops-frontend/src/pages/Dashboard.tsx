/**
 * Dashboard Page
 */

export default function Dashboard() {
  return (
    <div className="container-main">
      <h2 className="text-3xl font-bold mb-6">Dashboard</h2>
      <div className="grid-auto">
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900">Total Invoices</h3>
          <p className="text-3xl font-bold text-blue-600 mt-2">0</p>
        </div>
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900">Pending Amount</h3>
          <p className="text-3xl font-bold text-green-600 mt-2">$0.00</p>
        </div>
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900">Hours Tracked</h3>
          <p className="text-3xl font-bold text-orange-600 mt-2">0</p>
        </div>
      </div>
    </div>
  );
}
