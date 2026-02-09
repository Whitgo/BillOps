/**
 * Project form validation schema
 */

import { z } from 'zod';

export const projectSchema = z.object({
  name: z.string().min(1, 'Project name is required').max(200, 'Name is too long'),
  client_id: z.string().min(1, 'Client is required'),
  description: z.string().max(500, 'Description is too long').optional().or(z.literal('')),
});

export type ProjectFormData = z.infer<typeof projectSchema>;
