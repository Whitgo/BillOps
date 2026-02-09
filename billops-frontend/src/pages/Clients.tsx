/**
 * Clients Page
 */

import { useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button, Input, Modal, Table, Loader } from '@/components/ui';
import { clientSchema, ClientFormData } from '@/schemas/client';
import { useClients, useCreateClient, useUpdateClient, useDeleteClient } from '@/services/queries/hooks';
import type { Client } from '@/types/client';

const PAGE_SIZE = 10;

export default function Clients() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);

  const skip = (page - 1) * PAGE_SIZE;
  const { data, isLoading } = useClients(skip, PAGE_SIZE);
  const createClient = useCreateClient();
  const updateClient = useUpdateClient();
  const deleteClient = useDeleteClient();

  const items = useMemo(() => {
    const raw = (data as { data?: unknown })?.data;
    if (Array.isArray(raw)) return raw as Client[];
    if (raw && typeof raw === 'object' && 'items' in (raw as Record<string, unknown>)) {
      return ((raw as { items?: Client[] }).items || []) as Client[];
    }
    return [] as Client[];
  }, [data]);

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return items;
    return items.filter((client) =>
      [client.name, client.contact_email, client.contact_name]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(term))
    );
  }, [items, search]);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ClientFormData>({
    resolver: zodResolver(clientSchema),
  });

  const openCreate = () => {
    setSelectedClient(null);
    reset({ name: '', currency: 'USD', contact_email: '', contact_name: '' });
    setIsModalOpen(true);
  };

  const openEdit = (client: Client) => {
    setSelectedClient(client);
    reset({
      name: client.name || '',
      currency: client.currency || 'USD',
      contact_email: client.contact_email || '',
      contact_name: client.contact_name || '',
    });
    setIsModalOpen(true);
  };

  const openDelete = (client: Client) => {
    setSelectedClient(client);
    setIsDeleteOpen(true);
  };

  const onSubmit = async (formData: ClientFormData) => {
    if (selectedClient) {
      await updateClient.mutateAsync({ id: selectedClient.id, data: formData });
    } else {
      await createClient.mutateAsync(formData);
    }
    setIsModalOpen(false);
  };

  const onDelete = async () => {
    if (selectedClient) {
      await deleteClient.mutateAsync(selectedClient.id);
    }
    setIsDeleteOpen(false);
  };

  return (
    <div className="container-main space-y-6">
      <div className="flex-between flex-wrap gap-4">
        <h2 className="text-3xl font-bold">Clients</h2>
        <Button onClick={openCreate}>+ New Client</Button>
      </div>

      <div className="flex flex-col md:flex-row gap-4 md:items-center">
        <div className="flex-1">
          <Input
            placeholder="Search clients by name or email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="text-sm text-gray-600">
          Page {page}
        </div>
      </div>

      <div className="card">
        {isLoading ? (
          <div className="flex-center py-12">
            <Loader />
          </div>
        ) : (
          <Table headers={['Name', 'Email', 'Currency', 'Actions']}>
            {filtered.map((client) => (
              <tr key={client.id}>
                <td className="px-6 py-4 text-sm font-medium text-gray-900">{client.name}</td>
                <td className="px-6 py-4 text-sm text-gray-600">{client.contact_email || '—'}</td>
                <td className="px-6 py-4 text-sm text-gray-600">{client.currency || '—'}</td>
                <td className="px-6 py-4 text-sm">
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => openEdit(client)}>
                      Edit
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => openDelete(client)}>
                      Delete
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </Table>
        )}
      </div>

      <div className="flex-between">
        <Button
          variant="outline"
          size="sm"
          disabled={page === 1}
          onClick={() => setPage((p) => Math.max(1, p - 1))}
        >
          Previous
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={filtered.length < PAGE_SIZE}
          onClick={() => setPage((p) => p + 1)}
        >
          Next
        </Button>
      </div>

      {/* Create/Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={selectedClient ? 'Edit Client' : 'New Client'}
      >
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input
            label="Client Name"
            placeholder="Acme Corp"
            {...register('name')}
            error={errors.name?.message}
          />
          <Input
            label="Currency"
            placeholder="USD"
            {...register('currency')}
            error={errors.currency?.message}
          />
          <Input
            label="Contact Email"
            placeholder="contact@acme.com"
            {...register('contact_email')}
            error={errors.contact_email?.message}
          />
          <Input
            label="Contact Name"
            placeholder="Jane Doe"
            {...register('contact_name')}
            error={errors.contact_name?.message}
          />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" type="button" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={createClient.isPending || updateClient.isPending}>
              {selectedClient ? 'Save Changes' : 'Create Client'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Modal */}
      <Modal isOpen={isDeleteOpen} onClose={() => setIsDeleteOpen(false)} title="Delete Client">
        <p className="text-sm text-gray-600 mb-4">
          Are you sure you want to delete <strong>{selectedClient?.name}</strong>? This action cannot be undone.
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setIsDeleteOpen(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={onDelete}>
            Delete
          </Button>
        </div>
      </Modal>
    </div>
  );
}
