# Crypto News Agent - Frontend

The frontend is built with [Vite](https://vitejs.dev/), [React](https://reactjs.org/), [TypeScript](https://www.typescriptlang.org/), [TanStack Query](https://tanstack.com/query), [TanStack Router](https://tanstack.com/router), and [Shadcn UI](https://ui.shadcn.com/) + [Tailwind CSS](https://tailwindcss.com/).

## Technology Stack

- **React 18** - UI library with hooks
- **TypeScript** - Type-safe JavaScript
- **Vite** - Fast build tool and dev server
- **TanStack Query** - Data fetching and caching
- **TanStack Router** - File-based routing
- **Shadcn UI** - Composable UI components
- **Tailwind CSS** - Utility-first CSS framework
- **Playwright** - End-to-end testing

## Frontend Development

### Prerequisites

Before you begin, ensure that you have either the Node Version Manager (nvm) or Fast Node Manager (fnm) installed on your system.

* To install fnm follow the [official fnm guide](https://github.com/Schniz/fnm#installation). If you prefer nvm, you can install it using the [official nvm guide](https://github.com/nvm-sh/nvm#installing-and-updating).

### Setup

1. Navigate to the `frontend` directory:

```bash
cd frontend
```

2. If the Node.js version specified in the `.nvmrc` file isn't installed on your system, install it:

```bash
# If using fnm
fnm install

# If using nvm
nvm install
```

3. Switch to the installed version:

```bash
# If using fnm
fnm use

# If using nvm
nvm use
```

4. Install NPM packages:

```bash
npm install
```

5. Start the development server:

```bash
npm run dev
```

6. Open your browser at http://localhost:5173/

**Note**: This local development server is not running inside Docker - it's for rapid development with hot module replacement (HMR). This is the recommended workflow for frontend development. Once you're happy with your changes, you can test them in the Docker environment.

Check the file `package.json` to see other available options.

## Generate API Client

The frontend uses an auto-generated TypeScript client for the backend API. Regenerate it whenever the backend API changes:

### Automatically (Recommended)

From the project root directory, run:

```bash
./scripts/generate-client.sh
```

Then commit the changes.

### Manually

1. Start the Docker Compose stack to ensure the backend is running

2. Download the OpenAPI JSON file:

```bash
curl http://localhost:8000/openapi.json > frontend/openapi.json
```

3. Generate the frontend client:

```bash
npm run generate-client
```

4. Commit the changes

**Important**: Every time the backend changes (updating the OpenAPI schema), you should regenerate the frontend client using one of these methods.

## Using a Remote API

If you want to use a remote API instead of the local Docker backend, set the `VITE_API_URL` environment variable in `frontend/.env`:

```env
VITE_API_URL=https://api.my-domain.example.com
```

Then, when you run the frontend, it will use that URL as the base URL for all API calls.

## Code Structure

The frontend code is structured as follows:

```
frontend/src/
├── assets/          # Static assets (images, icons, etc.)
├── client/          # Auto-generated OpenAPI client (DO NOT EDIT)
├── components/      # Reusable UI components
│   ├── Chat/        # Chat interface components
│   ├── Common/      # Shared components (sidebar, nav, etc.)
│   ├── News/        # News table and article components
│   └── ui/          # Shadcn UI components
├── hooks/           # Custom React hooks
│   └── useWebSocket.ts  # WebSocket connection hook
├── routes/          # File-based routing (TanStack Router)
│   └── _layout/     # Layout route with nested pages
│       ├── index.tsx    # Home page
│       ├── chat.tsx     # Chat page
│       └── news.tsx     # News page
├── types/           # TypeScript type definitions
├── lib/             # Utility functions
├── index.css        # Global styles (Tailwind)
├── main.tsx         # Application entry point
└── routeTree.gen.ts # Auto-generated route tree (DO NOT EDIT)
```

### Key Files:

- **`client/`** - Auto-generated from backend OpenAPI schema. Never edit manually.
- **`routes/`** - File-based routing powered by TanStack Router. Add new pages here.
- **`components/ui/`** - Shadcn UI components. Add more using `npx shadcn@latest add <component>`.
- **`routeTree.gen.ts`** - Auto-generated route configuration. Never edit manually.

## End-to-End Testing with Playwright

The frontend includes E2E tests using Playwright.

### Running Tests

1. Start the Docker Compose stack (backend must be running):

```bash
docker compose up -d --wait backend
```

2. Run the tests:

```bash
npx playwright test
```

3. Run tests in UI mode to see the browser:

```bash
npx playwright test --ui
```

4. Clean up after tests:

```bash
docker compose down -v
```

### Writing Tests

To update tests, navigate to the `tests/` directory and modify existing test files or add new ones as needed.

For more information on writing and running Playwright tests, refer to the official [Playwright documentation](https://playwright.dev/docs/intro).

## Adding Shadcn UI Components

This project uses [Shadcn UI](https://ui.shadcn.com/) for UI components. To add a new component:

```bash
npx shadcn@latest add <component-name>
```

Example:
```bash
npx shadcn@latest add dialog
npx shadcn@latest add dropdown-menu
npx shadcn@latest add tabs
```

Components will be added to `src/components/ui/` and can be customized as needed.

## Available Scripts

- `npm run dev` - Start Vite dev server with HMR
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally
- `npm run lint` - Run Biome linter and formatter
- `npm run generate-client` - Generate API client from OpenAPI schema
- `npx playwright test` - Run E2E tests
- `npx playwright test --ui` - Run E2E tests in UI mode

## Development Workflow

1. **Start Docker services** (backend, database, Ollama):
   ```bash
   docker compose up -d
   ```

2. **Stop the frontend Docker service** (to run locally):
   ```bash
   docker compose stop frontend
   ```

3. **Start local dev server**:
   ```bash
   npm run dev
   ```

4. **Make changes** - Vite HMR will automatically reload

5. **Regenerate API client** (if backend changed):
   ```bash
   ./scripts/generate-client.sh
   ```

6. **Run tests**:
   ```bash
   npx playwright test
   ```

This workflow gives you the fastest development experience with instant hot module replacement while still using the Docker backend services.
