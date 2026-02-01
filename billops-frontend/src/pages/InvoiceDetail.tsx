/**
 * Invoice Detail Page
 */

import { useParams } from 'react-router-dom';

export default function InvoiceDetail() {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="container-main">
      <h2 className="text-3xl font-bold mb-6">Invoice #{id}</h2>
      <div className="card">
        <p className="text-gray-600">Invoice details will be loaded here.</p>
      </div>
    </div>
  );
}
