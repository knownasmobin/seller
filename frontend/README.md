# Frontend Admin Dashboard

React + Vite admin dashboard for the VPN Seller Bot project.

This app is used by admins to manage plans, orders, endpoints, broadcasts, and settings through backend APIs.

## Features

- Admin authentication with token persistence in `localStorage`
- Management pages for core operations:
  - `Dashboard`
  - `Plans`
  - `Orders`
  - `Endpoints`
  - `Broadcast`
  - `Settings`
- API helper with automatic bearer authentication header
- Automatic logout flow on `401 Unauthorized`

## Tech Stack

- React 19
- Vite 7
- React Router 7
- Lucide React
- ESLint 9

## Environment Variables

Create a `.env` file in `frontend/` to override the default API base URL:

```env
VITE_API_URL=http://localhost:3000/api/v1
```

If `VITE_API_URL` is not set, the app uses:

```text
/api/v1
```

## Local Development

### 1) Install dependencies

```bash
npm install
```

### 2) Start development server

```bash
npm run dev
```

### 3) Build for production

```bash
npm run build
```

### 4) Preview production build

```bash
npm run preview
```

### 5) Run linter

```bash
npm run lint
```

## Docker

Build and run from the `frontend/` directory:

```bash
docker build -t seller-frontend .
docker run -p 8085:80 seller-frontend
```

## Project Structure

```text
src/
  components/
    Sidebar.jsx
  pages/
    Dashboard.jsx
    Plans.jsx
    Orders.jsx
    Endpoints.jsx
    Broadcast.jsx
    Settings.jsx
    Login.jsx
  api.js
  App.jsx
  main.jsx
```

## Notes

- Authentication state is managed in `src/App.jsx`.
- API base URL and auth logic are centralized in `src/api.js`.
- In full deployment, this frontend is typically served through the repository’s root Docker/Nginx setup.
