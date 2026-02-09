import { z } from 'zod';

export const timeEntryFormSchema = z.object({
  started_at: z.string().min(1, 'Start time is required'),
  ended_at: z.string().min(1, 'End time is required'),
  project_id: z.string().optional(),
  client_id: z.string().optional(),
  activity_type: z.string().optional(),
  notes: z.string().optional(),
}).refine(
  (data) => {
    if (!data.started_at || !data.ended_at) return true;
    return new Date(data.started_at) < new Date(data.ended_at);
  },
  {
    message: 'End time must be after start time',
    path: ['ended_at'],
  }
);

export const timeEntryUpdateSchema = z.object({
  status: z.enum(['approved', 'rejected']),
  project_id: z.string().optional(),
  client_id: z.string().optional(),
  activity_type: z.string().optional(),
  notes: z.string().optional(),
});

export type TimeEntryFormData = z.infer<typeof timeEntryFormSchema>;
export type TimeEntryUpdateData = z.infer<typeof timeEntryUpdateSchema>;
