# SlideGen Frontend

Modern React frontend for SlideGen - AI-powered presentation generation platform.

## Technology Stack

- **Framework**: React 18+ with TypeScript
- **Build Tool**: Vite
- **State Management**: Zustand + TanStack Query (React Query)
- **UI Library**: Ant Design 5.x
- **HTTP Client**: Axios
- **Routing**: React Router v6
- **Form Management**: Ant Design Form

## Features

### Currently Implemented (Phase 1-3)

- ✅ Project setup with Vite, TypeScript, and all dependencies
- ✅ Complete TypeScript type definitions matching backend models
- ✅ Axios HTTP client with JWT interceptors
- ✅ API endpoint modules for all backend services
- ✅ Zustand stores for authentication and UI state
- ✅ React Router configuration with protected routes
- ✅ Authentication pages (Login/Signup) with form validation
- ✅ Authentication flow with JWT token management

### Planned Implementation

- 🔄 Layout components (Header, Sidebar, Dashboard)
- 🔄 LLM and Embedding configuration management UI
- 🔄 Session and file management interfaces
- 🔄 PPT generation workflow with SSE streaming
- 🔄 Markdown editor and PPTX export
- 🔄 Responsive design and polish

## Quick Start

### Prerequisites

- Node.js 18+ and npm
- Backend server running on http://127.0.0.1:7860

### Installation

```bash
# Navigate to web directory
cd web

# Install dependencies
npm install
```

### Development

```bash
# Start development server
npm run dev

# Server will start on http://localhost:5173
```

### Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
web/
├── src/
│   ├── api/                    # API client layer
│   │   ├── client.ts           # Axios instance with JWT
│   │   ├── endpoints/          # API endpoint modules
│   │   └── types/              # TypeScript interfaces
│   ├── components/             # React components
│   │   ├── common/             # Shared components
│   │   ├── auth/               # Auth components
│   │   ├── config/             # Config components
│   │   └── ...
│   ├── hooks/                  # Custom React hooks
│   ├── pages/                  # Route pages
│   ├── store/                  # Zustand stores
│   ├── utils/                  # Utility functions
│   ├── App.tsx                 # Main app component
│   ├── main.tsx                # Entry point
│   └── router.tsx              # Route configuration
├── .env.example                # Environment variables template
├── .env.development            # Development environment
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## Environment Variables

Create a `.env.local` file to override defaults:

```bash
# API Configuration
VITE_API_BASE_URL=http://127.0.0.1:7860

# Application Name
VITE_APP_NAME=SlideGen
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint (if configured)

## API Integration

The frontend communicates with the backend API at:

- **Default**: http://127.0.0.1:7860
- **Configurable**: Set `VITE_API_BASE_URL` in `.env.local`

### Authentication

- JWT tokens are stored in localStorage
- Axios interceptor automatically adds `Authorization` header
- 401 responses trigger automatic logout and redirect to login

### API Endpoints

All API endpoints are defined in `src/utils/constants.ts` and accessed through the endpoint modules in `src/api/endpoints/`.

## State Management

### Zustand Stores

- **authStore**: JWT token, user info, authentication state
- **uiStore**: Sidebar collapse, theme preferences
- **generationStore**: PPT generation workflow state

### React Query

Used for server state management:

- Automatic caching and refetching
- Loading and error states
- Optimistic updates
- Query invalidation

## Development Notes

### Code Organization

- Use functional components with hooks
- TypeScript strict mode enabled
- Follow existing patterns for consistency
- API types match backend Pydantic models

### Authentication Flow

1. User submits login form
2. Frontend calls `/api/v1/auth/login` with credentials
3. Backend returns JWT token
4. Token stored in Zustand store and localStorage
5. Axios interceptor adds token to all subsequent requests
6. Protected routes check authentication state

### Adding New Features

1. Define TypeScript types in `src/api/types/`
2. Create API endpoint in `src/api/endpoints/`
3. Create React Query hook in `src/hooks/`
4. Create components in `src/components/`
5. Create page in `src/pages/`
6. Add route in `src/router.tsx`

## Testing with Backend

1. Start the backend server:
   ```bash
   python main.py
   ```

2. Start the frontend dev server:
   ```bash
   cd web
   npm run dev
   ```

3. Open http://localhost:5173 in your browser

4. Create an account or login with existing credentials

## Troubleshooting

### CORS Issues

If you encounter CORS errors:

- Ensure backend CORS is configured to allow http://localhost:5173
- Check `vite.config.ts` proxy configuration
- Verify `VITE_API_BASE_URL` is correct

### Build Errors

If TypeScript compilation fails:

- Run `npm install` to ensure all dependencies are installed
- Check for missing type definitions
- Verify import paths are correct

### Authentication Issues

If login doesn't work:

- Check browser console for error messages
- Verify backend is running and accessible
- Check that credentials are correct
- Clear localStorage and try again

## Next Steps

To continue implementing the remaining phases:

1. **Phase 4**: Implement Layout components and Dashboard
2. **Phase 5**: Build configuration management interfaces
3. **Phase 6**: Add session and file management
4. **Phase 7**: Implement PPT generation workflow with streaming
5. **Phase 8**: Polish UI/UX and add responsive design

## License

This project is part of SlideGen - see the main project README for license information.
