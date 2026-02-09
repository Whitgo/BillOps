import { useState, useMemo } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Loader, Modal, Button, Input, SelectDropdown } from '@/components/ui';
import {
  usePendingTimeEntries,
  useApproveTimeEntry,
  useRejectTimeEntry,
  useCreateTimeEntry,
  useIngestActivitySignals,
  useIngestTaskStatus,
} from '@/services/queries/hooks';
import { useProjects } from '@/services/queries/hooks';
import { useClients } from '@/services/queries/hooks';
import { timeEntryFormSchema, type TimeEntryFormData } from '@/schemas/timeEntry';
import type { TimeEntry } from '@/types/timeEntry';
import { AlertCircle, CheckCircle, XCircle, Clock, Plus } from 'lucide-react';

const PAGE_SIZE = 10;

export default function TimeCapture() {
  const [page, setPage] = useState(1);
  const [isManualModalOpen, setIsManualModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [selectedEntry, setSelectedEntry] = useState<TimeEntry | null>(null);
  const [ingestTaskId, setIngestTaskId] = useState<string | null>(null);

  // Fetch pending time entries with polling
  const { data: timeEntriesData, isLoading: entriesLoading } = usePendingTimeEntries(
    (page - 1) * PAGE_SIZE,
    PAGE_SIZE
  );

  // Fetch clients and projects for dropdowns
  const { data: projectsData } = useProjects(0, 100);
  const { data: clientsData } = useClients(0, 100);

  // Mutations
  const approveEntry = useApproveTimeEntry();
  const rejectEntry = useRejectTimeEntry();
  const createEntry = useCreateTimeEntry();
  const ingestSignals = useIngestActivitySignals();
  const { data: ingestStatus, isLoading: statusLoading } = useIngestTaskStatus(ingestTaskId);

  // Form setup for manual entry
  const manualForm = useForm<TimeEntryFormData>({
    resolver: zodResolver(timeEntryFormSchema),
    defaultValues: {
      started_at: '',
      ended_at: '',
      project_id: '',
      client_id: '',
      activity_type: 'focused_work',
      notes: '',
    },
  });

  // Form setup for edit entry
  const editForm = useForm<TimeEntryFormData>({
    resolver: zodResolver(timeEntryFormSchema),
    defaultValues: {
      started_at: '',
      ended_at: '',
      project_id: '',
      client_id: '',
      activity_type: '',
      notes: '',
    },
  });

  const entries = timeEntriesData?.entries || [];
  const total = timeEntriesData?.total || 0;

  // Memoized project and client lookup maps
  const projectMap = useMemo(
    () =>
      new Map(
        (projectsData?.items || []).map((p) => [p.id, p])
      ),
    [projectsData]
  );

  const clientMap = useMemo(
    () =>
      new Map(
        (clientsData?.items || []).map((c) => [c.id, c])
      ),
    [clientsData]
  );

  // Handle approve
  const handleApprove = async (entry: TimeEntry) => {
    try {
      await approveEntry.mutateAsync({
        id: entry.id,
        entry: {
          status: 'approved',
          project_id: entry.project_id,
          client_id: entry.client_id,
          activity_type: entry.activity_type,
          notes: entry.notes,
        },
      });
    } catch (error) {
      console.error('Failed to approve entry:', error);
    }
  };

  // Handle reject
  const handleReject = async (entry: TimeEntry) => {
    try {
      await rejectEntry.mutateAsync({
        id: entry.id,
        entry: {
          status: 'rejected',
        },
      });
    } catch (error) {
      console.error('Failed to reject entry:', error);
    }
  };

  // Handle edit
  const handleEdit = (entry: TimeEntry) => {
    setSelectedEntry(entry);
    editForm.reset({
      started_at: entry.started_at,
      ended_at: entry.ended_at,
      project_id: entry.project_id || '',
      client_id: entry.client_id || '',
      activity_type: entry.activity_type || 'focused_work',
      notes: entry.notes || '',
    });
    setIsEditModalOpen(true);
  };

  // Handle edit submit
  const onEditSubmit = async (data: TimeEntryFormData) => {
    if (!selectedEntry) return;
    try {
      await approveEntry.mutateAsync({
        id: selectedEntry.id,
        entry: {
          status: 'approved',
          project_id: data.project_id,
          client_id: data.client_id,
          activity_type: data.activity_type,
          notes: data.notes,
        },
      });
      setIsEditModalOpen(false);
      setSelectedEntry(null);
      editForm.reset();
    } catch (error) {
      console.error('Failed to update entry:', error);
    }
  };

  // Handle manual entry submit
  const onManualSubmit = async (data: TimeEntryFormData) => {
    try {
      await createEntry.mutateAsync(data);
      setIsManualModalOpen(false);
      manualForm.reset({
        started_at: '',
        ended_at: '',
        project_id: '',
        client_id: '',
        activity_type: 'focused_work',
        notes: '',
      });
    } catch (error) {
      console.error('Failed to create entry:', error);
    }
  };

  // Handle ingest activity signals (simulated)
  const handleIngestSignals = async () => {
    try {
      // Simulated activity signals - in real app, these would come from tracking service
      const simulatedSignals = [
        {
          timestamp: new Date().toISOString(),
          app: 'vscode',
          type: 'keyboard',
          source_type: 'keyboard',
        },
        {
          timestamp: new Date(Date.now() - 15 * 60000).toISOString(),
          app: 'vscode',
          type: 'keyboard',
          source_type: 'keyboard',
        },
      ];

      const result = await ingestSignals.mutateAsync(simulatedSignals);
      setIngestTaskId(result?.data?.task_id || '');
    } catch (error) {
      console.error('Failed to ingest signals:', error);
    }
  };

  // Format duration
  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  // Format date time
  const formatDateTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleString();
  };

  return (
    <div className="space-y-6">
      {/* Header with Actions */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Time Capture</h1>
          <p className="mt-1 text-gray-600">
            Review and approve suggested time entries from activity tracking
          </p>
        </div>
        <div className="flex gap-3">
          <Button
            onClick={handleIngestSignals}
            disabled={ingestSignals.isPending}
            className="flex items-center gap-2"
          >
            {ingestSignals.isPending ? (
              <>
                <Loader className="w-4 h-4" />
                Ingesting...
              </>
            ) : (
              <>
                <AlertCircle className="w-4 h-4" />
                Get Suggestions
              </>
            )}
          </Button>
          <Button variant="secondary" onClick={() => setIsManualModalOpen(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Add Manual Entry
          </Button>
        </div>
      </div>

      {/* Ingest Status */}
      {ingestTaskId && (
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {statusLoading && <Loader className="w-5 h-5 text-blue-600" />}
              <div>
                <p className="font-medium text-blue-900">
                  {statusLoading ? 'Processing activity signals...' : 'Processing complete'}
                </p>
                <p className="text-sm text-blue-700">
                  {ingestStatus?.status === 'SUCCESS'
                    ? `Created ${ingestStatus.result?.created_count || 0} new entries`
                    : 'Analyzing your activity signals...'}
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIngestTaskId(null)}
            >
              Dismiss
            </Button>
          </div>
        </div>
      )}

      {/* Pending Entries List */}
      <div className="bg-white shadow rounded-lg">
        {entriesLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <Loader className="w-8 h-8 mx-auto mb-2 text-gray-400" />
              <p className="text-gray-600">Loading time entries...</p>
            </div>
          </div>
        ) : entries.length === 0 ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <Clock className="w-12 h-12 mx-auto mb-2 text-gray-400" />
              <p className="text-gray-600">No pending time entries to review</p>
              <p className="text-sm text-gray-500 mt-1">
                Click "Get Suggestions" to generate entries from activity signals
              </p>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                    Time Period
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                    Project
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                    Client
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                    Confidence
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {entries.map((entry) => {
                  const project = entry.project_id ? projectMap.get(entry.project_id) : null;
                  const client = entry.client_id ? clientMap.get(entry.client_id) : null;
                  const confidence = entry.context_data?.confidence || 0.9;

                  return (
                    <tr key={entry.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium bg-blue-50 text-blue-700">
                          <Clock className="w-4 h-4" />
                          {formatDuration(entry.duration_minutes)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <div>
                          <p>{formatDateTime(entry.started_at)}</p>
                          <p className="text-xs text-gray-500">
                            to {new Date(entry.ended_at).toLocaleTimeString()}
                          </p>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {project?.name || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {client?.name || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <div className="flex-1 bg-gray-200 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${
                                confidence > 0.7
                                  ? 'bg-green-500'
                                  : confidence > 0.4
                                  ? 'bg-yellow-500'
                                  : 'bg-red-500'
                              }`}
                              style={{ width: `${confidence * 100}%` }}
                            />
                          </div>
                          <span className="text-xs font-medium text-gray-600 min-w-fit">
                            {Math.round(confidence * 100)}%
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <div className="flex items-center gap-2">
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => handleEdit(entry)}
                            disabled={approveEntry.isPending}
                          >
                            Edit
                          </Button>
                          <Button
                            size="sm"
                            variant="secondary"
                            className="text-green-600 hover:bg-green-50"
                            onClick={() => handleApprove(entry)}
                            disabled={approveEntry.isPending}
                          >
                            <CheckCircle className="w-4 h-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="secondary"
                            className="text-red-600 hover:bg-red-50"
                            onClick={() => handleReject(entry)}
                            disabled={rejectEntry.isPending}
                          >
                            <XCircle className="w-4 h-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {total > PAGE_SIZE && (
          <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
            <p className="text-sm text-gray-600">
              Showing {(page - 1) * PAGE_SIZE + 1} to {Math.min(page * PAGE_SIZE, total)} of{' '}
              {total} entries
            </p>
            <div className="flex gap-2">
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
                disabled={page * PAGE_SIZE >= total}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Manual Entry Modal */}
      <Modal
        isOpen={isManualModalOpen}
        onClose={() => {
          setIsManualModalOpen(false);
          manualForm.reset();
        }}
        title="Add Manual Time Entry"
        size="md"
      >
        <form onSubmit={manualForm.handleSubmit(onManualSubmit)} className="space-y-4">
          <Controller
            name="started_at"
            control={manualForm.control}
            render={({ field, fieldState }) => (
              <Input
                {...field}
                type="datetime-local"
                label="Start Time"
                error={fieldState.error?.message}
              />
            )}
          />

          <Controller
            name="ended_at"
            control={manualForm.control}
            render={({ field, fieldState }) => (
              <Input
                {...field}
                type="datetime-local"
                label="End Time"
                error={fieldState.error?.message}
              />
            )}
          />

          <Controller
            name="client_id"
            control={manualForm.control}
            render={({ field: { value, onChange } }) => (
              <SelectDropdown
                label="Client (Optional)"
                value={value}
                onChange={onChange}
                options={
                  clientsData?.items.map((c) => ({
                    label: c.name,
                    value: c.id,
                  })) || []
                }
                placeholder="Select a client"
                allowEmpty
              />
            )}
          />

          <Controller
            name="project_id"
            control={manualForm.control}
            render={({ field: { value, onChange } }) => (
              <SelectDropdown
                label="Project (Optional)"
                value={value}
                onChange={onChange}
                options={
                  projectsData?.items.map((p) => ({
                    label: p.name,
                    value: p.id,
                  })) || []
                }
                placeholder="Select a project"
                allowEmpty
              />
            )}
          />

          <Controller
            name="activity_type"
            control={manualForm.control}
            render={({ field: { value, onChange } }) => (
              <SelectDropdown
                label="Activity Type"
                value={value}
                onChange={onChange}
                options={[
                  { label: 'Focused Work', value: 'focused_work' },
                  { label: 'Research', value: 'research' },
                  { label: 'Communication', value: 'communication' },
                  { label: 'Admin', value: 'admin' },
                  { label: 'Break', value: 'break' },
                ]}
              />
            )}
          />

          <Controller
            name="notes"
            control={manualForm.control}
            render={({ field, fieldState }) => (
              <Input
                {...field}
                type="text"
                label="Notes (Optional)"
                placeholder="What did you work on?"
                error={fieldState.error?.message}
              />
            )}
          />

          <div className="flex gap-3 pt-4">
            <Button
              type="submit"
              disabled={createEntry.isPending}
              className="flex-1"
            >
              {createEntry.isPending ? 'Creating...' : 'Create Entry'}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setIsManualModalOpen(false);
                manualForm.reset();
              }}
              className="flex-1"
            >
              Cancel
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit Entry Modal */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => {
          setIsEditModalOpen(false);
          setSelectedEntry(null);
        }}
        title="Edit Time Entry"
        size="md"
      >
        <form onSubmit={editForm.handleSubmit(onEditSubmit)} className="space-y-4">
          <Controller
            name="started_at"
            control={editForm.control}
            render={({ field, fieldState }) => (
              <Input
                {...field}
                type="datetime-local"
                label="Start Time"
                error={fieldState.error?.message}
              />
            )}
          />

          <Controller
            name="ended_at"
            control={editForm.control}
            render={({ field, fieldState }) => (
              <Input
                {...field}
                type="datetime-local"
                label="End Time"
                error={fieldState.error?.message}
              />
            )}
          />

          <Controller
            name="client_id"
            control={editForm.control}
            render={({ field: { value, onChange } }) => (
              <SelectDropdown
                label="Client (Optional)"
                value={value}
                onChange={onChange}
                options={
                  clientsData?.items.map((c) => ({
                    label: c.name,
                    value: c.id,
                  })) || []
                }
                placeholder="Select a client"
                allowEmpty
              />
            )}
          />

          <Controller
            name="project_id"
            control={editForm.control}
            render={({ field: { value, onChange } }) => (
              <SelectDropdown
                label="Project (Optional)"
                value={value}
                onChange={onChange}
                options={
                  projectsData?.items.map((p) => ({
                    label: p.name,
                    value: p.id,
                  })) || []
                }
                placeholder="Select a project"
                allowEmpty
              />
            )}
          />

          <Controller
            name="activity_type"
            control={editForm.control}
            render={({ field: { value, onChange } }) => (
              <SelectDropdown
                label="Activity Type"
                value={value}
                onChange={onChange}
                options={[
                  { label: 'Focused Work', value: 'focused_work' },
                  { label: 'Research', value: 'research' },
                  { label: 'Communication', value: 'communication' },
                  { label: 'Admin', value: 'admin' },
                  { label: 'Break', value: 'break' },
                ]}
              />
            )}
          />

          <Controller
            name="notes"
            control={editForm.control}
            render={({ field, fieldState }) => (
              <Input
                {...field}
                type="text"
                label="Notes"
                placeholder="What did you work on?"
                error={fieldState.error?.message}
              />
            )}
          />

          <div className="flex gap-3 pt-4">
            <Button
              type="submit"
              disabled={approveEntry.isPending}
              className="flex-1"
            >
              {approveEntry.isPending ? 'Saving...' : 'Save & Approve'}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setIsEditModalOpen(false);
                setSelectedEntry(null);
              }}
              className="flex-1"
            >
              Cancel
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

