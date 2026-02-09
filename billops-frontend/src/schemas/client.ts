/**
 * Client form validation schema
 */

import { z } from 'zod';

export const clientSchema = z.object({
  name: z.string().min(1, 'Client name is required').max(200, 'Name is too long'),
  currency: z.string().min(1, 'Currency is required').max(10).optional().or(z.literal('')),
  contact_email: z.string().email('Invalid email').optional().or(z.literal('')),
  contact_name: z.string().max(200, 'Contact name is too long').optional().or(z.literal('')),
});

export type ClientFormData = z.infer<typeof clientSchema>;
