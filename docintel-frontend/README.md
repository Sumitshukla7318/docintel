# DocIntel Frontend

React + Vite + TypeScript + Tailwind CSS frontend for the DocIntel agentic RAG platform.

## Setup

```bash
npm install
cp .env.example .env
# edit .env if your backend runs on a different port than 8001
npm run dev
```

Open the printed local URL (usually http://localhost:5173).

## Build for production

```bash
npm run build
```

Output goes to `dist/` — deploy as a static site anywhere (Vercel, Netlify, Nginx, or served directly by FastAPI).

## Structure

- `src/lib/api.ts` — axios client with automatic JWT refresh
- `src/context/AuthContext.tsx` — auth state (login/register/logout)
- `src/pages/` — route-level pages (Login, Register, Library, Chat)
- `src/components/documents/` — upload + document list UI
- `src/components/chat/` — chat sidebar, message bubbles, citations, composer
- `src/components/ui/` — hand-built shadcn-style primitives (Button, Input, Card, etc.)

Requires the DocIntel backend running and reachable at the URL set in `VITE_API_BASE_URL`.
