/**
 * Projects Page
 */

import { useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button, Input, Modal, Table, Loader } from '@/components/ui';
import { projectSchema, ProjectFormData } from '@/schemas/project';
import {
  useClients,
  useProjects,
  useCreateProject,
  useUpdateProject,
  useDeleteProject,
} from '@/services/queries/hooks';
import type { Project } from '@/types/project';
import type { Client } from '@/types/client';

const PAGE_SIZE = 10;

export default function Projects() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [clientFilter, setClientFilter] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);

  const skip = (page - 1) * PAGE_SIZE;
  const { data, isLoading } = useProjects(skip, PAGE_SIZE, clientFilter || undefined);
  const { data: clientsData } = useClients(0, 100);

  const createProject = useCreateProject();
  const updateProject = useUpdateProject();
  const deleteProject = useDeleteProject();

  const clients = useMemo(() => {
    const raw = (clientsData as { data?: unknown })?.data;
    if (Array.isArray(raw)) return raw as Client[];
    if (raw && typeof raw === 'object' && 'items' in (raw as Record<string, unknown>)) {
      return ((raw as { items?: Client[] }).items || []) as Client[];
    }
    return [] as Client[];
  }, [clientsData]);

  const items = useMemo(() => {
    const raw = (data as { data?: unknown })?.data;
    if (Array.isArray(raw)) return raw as Project[];
    if (raw && typeof raw === 'object' && 'items' in (raw as Record<string, unknown>)) {
      return ((raw as { items?: Project[] }).items || []) as Project[];
    }
    return [] as Project[];
  }, [data]);

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return items;
    return items.filter((project) =>
      [project.name, project.description]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(term))
    );
  }, [items, search]);

  const clientNameMap = useMemo(() => {
    return clients.reduce<Record<string, string>>((acc, client) => {
      acc[client.id] = client.name;
      return acc;
    }, {});
  }, [clients]);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ProjectFormData>({
    resolver: zodResolver(projectSchema),
  });

  const openCreate = () => {
    setSelectedProject(null);
    reset({ name: '', client_id: '', description: '' });
    setIsModalOpen(true);
  };

  const openEdit = (project: Project) => {
    setSelectedProject(project);
    reset({
      name: project.name || '',
      client_id: project.client_id || '',
      description: project.description || '',
    });
    setIsModalOpen(true);
  };

  const openDelete = (project: Project) => {
    setSelectedProject(project);
    setIsDeleteOpen(true);
  };

  const onSubmit = async (formData: ProjectFormData) => {
    if (selectedProject) {
      await updateProject.mutateAsync({ id: selectedProject.id, data: formData });
    } else {
      await createProject.mutateAsync(formData);
    }
    setIsModalOpen(false);
  };

  const onDelete = async () => {
    if (selectedProject) {
      await deleteProject.mutateAsync(selectedProject.id);
    }
    setIsDeleteOpen(false);
  };

  return (
    <div className="container-main space-y-6">
      <div className="flex-between flex-wrap gap-4">
        <h2 className="text-3xl font-bold">Projects</h2>
        <Button onClick={openCreate}>+ New Project</Button>
      </div>

      <div className="flex flex-col md:flex-row gap-4 md:items-center">
        <div className="flex-1">
          <Input
            placeholder="Search projects by name or description..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div>
          <select
            className="input"
            value={clientFilter}
            onChange={(e) => {
              setClientFilter(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All Clients</option>
            {clients.map((client) => (
              <option key={client.id} value={client.id}>
                {client.name}
              </option>
            ))}
          </select>
        </div>
        <div className="text-sm text-gray-600">Page {page}</div>
      </div>

      <div className="card">
        {isLoading ? (
          <div className="flex-center py-12">
            <Loader />
          </div>
        ) : (
          <Table headers={['Name', 'Client', 'Description', 'Actions']}>
            {filtered.map((project) => (
              <tr key={project.id}>
                <td className="px-6 py-4 text-sm font-medium text-gray-900">{project.name}</td>
                <td className="px-6 py-4 text-sm text-gray-600">
                  {project.client_id ? clientNameMap[project.client_id] || '—' : '—'}
                </td>
                <td className="px-6 py-4 text-sm text-gray-600">{project.description || '—'}</td>
                <td className="px-6 py-4 text-sm">
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => openEdit(project)}>
                      Edit
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => openDelete(project)}>
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
        title={selectedProject ? 'Edit Project' : 'New Project'}
      >
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input
            label="Project Name"
            placeholder="Website Redesign"
            {...register('name')}
            error={errors.name?.message}
          />
          <div className="space-y-2">
            <label className="label">Client</label>
            <select className="input" {...register('client_id')}>
              <option value="">Select a client</option>
              {clients.map((client) => (
                <option key={client.id} value={client.id}>
                  {client.name}
                </option>
              ))}
            </select>
            {errors.client_id?.message && (
              <p className="text-sm text-red-600">{errors.client_id.message}</p>
            )}
          </div>
          <Input
            label="Description"
            placeholder="Short description of the project"
            {...register('description')}
            error={errors.description?.message}
          />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" type="button" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={createProject.isPending || updateProject.isPending}>
              {selectedProject ? 'Save Changes' : 'Create Project'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Modal */}
      <Modal isOpen={isDeleteOpen} onClose={() => setIsDeleteOpen(false)} title="Delete Project">
        <p className="text-sm text-gray-600 mb-4">
          Are you sure you want to delete <strong>{selectedProject?.name}</strong>? This action cannot be undone.
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
