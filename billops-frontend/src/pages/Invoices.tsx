/**
 * Invoices List Page
 */

export default function Invoices() {
  return (
    <div className="container-main">
      <div className="flex-between mb-6">
        <h2 className="text-3xl font-bold">Invoices</h2>
        <button className="btn btn-primary">+ New Invoice</button>
      </div>
      <div className="card">
        <p className="text-gray-600">No invoices yet. Create your first invoice to get started.</p>
      </div>
    </div>
  );
}
