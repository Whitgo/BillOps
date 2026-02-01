# BillOps Frontend

A modern React + TypeScript frontend for the BillOps billing and invoicing application.

## 🚀 Tech Stack

- **React 18** - UI library
- **TypeScript 5** - Type safety
- **Vite 5** - Lightning-fast build tool
- **TailwindCSS 3** - Utility-first CSS
- **React Router 6** - Client-side routing
- **React Query (TanStack Query)** - Server state management
- **Axios** - HTTP client
- **ESLint & Prettier** - Code quality and formatting

## 📁 Project Structure

```
src/
├── app/                    # Application-level components
├── components/
│   ├── common/            # Reusable UI components
│   └── layouts/           # Layout components
├── config/                # Configuration files
├── constants/             # Application constants
├── features/              # Feature-specific modules
├── hooks/                 # Custom React hooks
├── pages/                 # Page components (routes)
├── routes/                # Route configuration
├── services/
│   ├── api/              # API client and endpoints
│   └── queries/          # React Query hooks
├── styles/                # Global styles and Tailwind
├── types/                 # TypeScript type definitions
└── utils/                 # Utility functions
```

## 🛠️ Setup Instructions

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
```

### Environment Variables

Create a `.env.local` file based on `.env.example`:

```env
VITE_API_URL=http://localhost:8000
VITE_API_TIMEOUT=30000
VITE_APP_NAME=BillOps
VITE_APP_VERSION=0.1.0
VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_DEBUG=false
```

## 📝 Available Scripts

### Development
```bash
npm run dev      # Start dev server (http://localhost:5173)
```

### Building
```bash
npm run build    # Build for production
npm run preview  # Preview production build locally
```

### Code Quality
```bash
npm run lint           # Run ESLint
npm run lint:fix       # Fix ESLint issues
npm run format         # Format code with Prettier
npm run type-check     # Check TypeScript types
```

## 🔌 API Integration

### HTTP Client

The API client is configured in `src/services/api/client.ts` with:
- Automatic request/response interceptors
- Auth token injection
- Error handling with retry logic
- Debug logging in development mode

### API Service

Use the `apiService` from `src/services/api/index.ts`:

```typescript
import { apiService, apiEndpoints } from '@/services/api';

// Fetch data
const data = await apiService.fetch(apiEndpoints.invoices.list);

// Create
await apiService.create(apiEndpoints.invoices.create, payload);

// Update
await apiService.update(apiEndpoints.invoices.update(id), payload);

// Delete
await apiService.delete(apiEndpoints.invoices.delete(id));
```

## ⚡ React Query

Server state management is handled by React Query with custom hooks in `src/services/queries/hooks.ts`:

```typescript
import { useInvoices, useCreateUser, useDeleteUser } from '@/services/queries/hooks';

// Fetch
const { data, isLoading, error } = useInvoices();

// Create
const mutation = useCreateUser();
await mutation.mutateAsync(userData);

// Delete
const deleteMutation = useDeleteUser();
await deleteMutation.mutateAsync(userId);
```

## 🎨 Styling

### TailwindCSS

Utility-first CSS framework configured with:
- Custom color palette (primary/secondary)
- Extended spacing and shadows
- Form component plugin
- Custom component classes in `globals.css`

### Custom Components

Pre-built Tailwind component classes:
- `.btn`, `.btn-primary`, `.btn-outline` - Buttons
- `.card` - Card containers
- `.input`, `.label` - Form controls
- `.container-main` - Main content container

## 🪝 Custom Hooks

### useApiError
Manage API error state:
```typescript
const { error, handleError, clearError } = useApiError();
```

### useLocalStorage
Persist state to localStorage:
```typescript
const [value, setValue] = useLocalStorage('key', initialValue);
```

### useAsync
Manage async function loading states:
```typescript
const { data, loading, error, execute } = useAsync(asyncFn);
```

## 🛣️ Routing

Routes are configured in `src/routes/index.tsx`. Lazy loading is used for page components to optimize bundle size.

Main routes:
- `/` - Home
- `/dashboard` - Dashboard
- `/invoices` - Invoices list
- `/invoices/:id` - Invoice detail
- `/time-capture` - Time tracking
- `/users` - User management
- `/settings` - Settings

## 📋 Path Aliases

TypeScript path aliases configured for cleaner imports:
- `@/*` → `src/*`
- `@components/*` → `src/components/*`
- `@services/*` → `src/services/*`
- `@utils/*` → `src/utils/*`
- `@hooks/*` → `src/hooks/*`
- And more...

## 🔐 Authentication

Auth token stored in localStorage:
```typescript
localStorage.setItem('authToken', token);

// Automatically injected in API requests
// HTTP client adds: Authorization: Bearer {token}
```

Unauthorized responses (401) automatically redirect to login.

## 🧪 Development Tips

### Enable Debug Mode

Set in `.env.local`:
```env
VITE_ENABLE_DEBUG=true
```

This enables:
- Detailed API request/response logging
- Enhanced error information in console

### Adding New Routes

1. Create page component in `src/pages/`
2. Add route to `src/routes/index.tsx`
3. Add navigation link to `src/components/common/Sidebar.tsx`

### Adding API Endpoints

1. Add endpoint to `apiEndpoints` object in `src/services/api/index.ts`
2. Create custom hooks if needed in `src/services/queries/hooks.ts`
3. Use in components with React Query

## 📦 Performance Optimizations

- Vite code splitting for vendor packages
- React Router lazy loading for pages
- React Query cache management
- Minified CSS and JS in production
- Automatic chunk splitting for better caching

## 🐛 Troubleshooting

### Port Already in Use
The dev server defaults to port 5173. To use a different port:
```bash
npm run dev -- --port 5174
```

### API Connection Issues
- Verify `VITE_API_URL` in `.env.local` matches your backend
- Check CORS configuration in backend if requests fail
- Enable debug mode to see detailed error logs

### TypeScript Errors
Run type-check to verify:
```bash
npm run type-check
```

## 📚 Additional Resources

- [Vite Documentation](https://vitejs.dev)
- [React Documentation](https://react.dev)
- [TailwindCSS Documentation](https://tailwindcss.com)
- [React Query Documentation](https://tanstack.com/query/latest)
- [React Router Documentation](https://reactrouter.com)
