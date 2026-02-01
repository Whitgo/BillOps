/**
 * Users Management Page
 */

export default function Users() {
  return (
    <div className="container-main">
      <div className="flex-between mb-6">
        <h2 className="text-3xl font-bold">Users</h2>
        <button className="btn btn-primary">+ Add User</button>
      </div>
      <div className="card">
        <p className="text-gray-600">No users found. Add your first user to get started.</p>
      </div>
    </div>
  );
}
