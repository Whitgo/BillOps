# Frontend Quick Reference

## 🚀 Getting Started

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Lint and format
npm run lint
npm run format
```

## 📂 Key File Locations

| Purpose | Location |
|---------|----------|
| API Configuration | `src/config/index.ts` |
| HTTP Client | `src/services/api/client.ts` |
| API Endpoints | `src/services/api/index.ts` |
| React Query Hooks | `src/services/queries/hooks.ts` |
| Routes | `src/routes/index.tsx` |
| Global Styles | `src/styles/globals.css` |
| TypeScript Config | `tsconfig.json` |
| Vite Config | `vite.config.ts` |

## 🎨 Common Tasks

### Create a New Page

1. Create component in `src/pages/MyPage.tsx`:
```typescript
export default function MyPage() {
  return (
    <div className="container-main">
      <h1>My Page</h1>
    </div>
  );
}
```

2. Add route to `src/routes/index.tsx`:
```typescript
{
  path: 'my-page',
  lazy: () => import('@/pages/MyPage').then(m => ({ Component: m.default })),
}
```

3. Add navigation link to `src/components/common/Sidebar.tsx`:
```typescript
{ label: 'My Page', path: '/my-page' }
```

### Fetch Data with React Query

```typescript
import { useQuery } from '@tanstack/react-query';
import { apiService, apiEndpoints } from '@/services/api';

function MyComponent() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['myData'],
    queryFn: () => apiService.fetch(apiEndpoints.users.list),
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error!</div>;
  
  return <div>{/* Use data */}</div>;
}
```

### Use Custom React Query Hooks

```typescript
import { useUsers, useCreateUser } from '@/services/queries/hooks';

function MyComponent() {
  const { data: users } = useUsers();
  const createMutation = useCreateUser();

  const handleCreate = async (userData) => {
    await createMutation.mutateAsync(userData);
  };

  return <div>{/* Render */}</div>;
}
```

### Create a Form Component

```typescript
import { useState } from 'react';

export default function MyForm() {
  const [data, setData] = useState({ name: '', email: '' });

  const handleSubmit = (e) => {
    e.preventDefault();
    // Handle submission
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="label">Name</label>
        <input
          type="text"
          className="input"
          value={data.name}
          onChange={(e) => setData({ ...data, name: e.target.value })}
        />
      </div>
      <button type="submit" className="btn btn-primary">
        Submit
      </button>
    </form>
  );
}
```

### Add API Endpoint

1. Add to `apiEndpoints` in `src/services/api/index.ts`:
```typescript
myFeature: {
  list: '/my-feature',
  get: (id: string) => `/my-feature/${id}`,
  create: '/my-feature',
}
```

2. Create React Query hook in `src/services/queries/hooks.ts`:
```typescript
export const useMyFeature = () => {
  return useQuery({
    queryKey: ['myFeature'],
    queryFn: () => apiService.fetch(apiEndpoints.myFeature.list),
  });
};
```

## 🎯 Styling Classes

### Buttons
```html
<button className="btn btn-primary">Primary</button>
<button className="btn btn-secondary">Secondary</button>
<button className="btn btn-outline">Outline</button>
<button className="btn btn-sm">Small</button>
<button className="btn btn-lg">Large</button>
```

### Cards
```html
<div className="card">
  <h3>Card Title</h3>
  <p>Card content</p>
</div>
```

### Forms
```html
<label className="label">Name</label>
<input className="input" type="text" />
<select className="input">
  <option>Option 1</option>
</select>
```

### Layout
```html
<div className="container-main">
  <div className="flex-center">Centered</div>
  <div className="flex-between">Space Between</div>
  <div className="grid-auto">Auto Grid</div>
</div>
```

## 🔍 Debugging

### Enable Debug Mode

Set in `.env.local`:
```env
VITE_ENABLE_DEBUG=true
```

### Check API Calls

1. Open browser DevTools → Network tab
2. Look for XHR requests to your API
3. Check response in Console (if debug mode enabled)

### TypeScript Errors

```bash
npm run type-check
```

## 📋 Path Aliases Reference

```typescript
import { something } from '@/utils';           // src/utils
import Component from '@components/MyComponent'; // src/components
import { useMyHook } from '@hooks';             // src/hooks
import { apiService } from '@services/api';     // src/services/api
import type { MyType } from '@types/api';       // src/types
import { MY_CONSTANT } from '@constants';       // src/constants
import Page from '@pages/MyPage';               // src/pages
import { useMyData } from '@features/myModule'; // src/features
```

## 🐛 Common Issues

### "Cannot find module" Error
- Check path alias in `tsconfig.json`
- Verify file path is correct
- Run `npm run type-check`

### Styles not applied
- Verify TailwindCSS class is in `content` array in `tailwind.config.ts`
- Check CSS is imported in component
- Clear build cache: `rm -rf dist && npm run build`

### API requests failing
- Check `VITE_API_URL` in `.env.local`
- Verify backend is running on expected port
- Enable debug mode to see detailed errors
- Check CORS configuration in backend

### Build errors
- Run `npm run type-check` to find TypeScript issues
- Run `npm run lint` to find linting issues
- Check `dist/` folder was created successfully

## 📚 Useful Commands

```bash
# Development
npm run dev              # Start dev server
npm run dev -- --open   # Start and open browser

# Building
npm run build            # Build for production
npm run preview          # Preview production build

# Code Quality
npm run lint             # Run ESLint
npm run lint:fix         # Auto-fix ESLint issues
npm run format           # Format with Prettier
npm run type-check       # Check TypeScript types

# Cleanup
rm -rf dist node_modules   # Full cleanup
npm install                 # Reinstall
```

## 🔗 Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| VITE_API_URL | `http://localhost:8000` | Backend API base URL |
| VITE_API_TIMEOUT | `30000` | API request timeout (ms) |
| VITE_APP_NAME | `BillOps` | App name |
| VITE_APP_VERSION | `0.1.0` | App version |
| VITE_ENABLE_ANALYTICS | `false` | Enable analytics |
| VITE_ENABLE_DEBUG | `false` | Enable debug logging |

## 📖 Learn More

- [Vite Docs](https://vitejs.dev)
- [React Docs](https://react.dev)
- [TailwindCSS Docs](https://tailwindcss.com)
- [React Query Docs](https://tanstack.com/query/latest)
- [React Router Docs](https://reactrouter.com)
- [Axios Docs](https://axios-http.com)
