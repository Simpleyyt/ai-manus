# webdev_init_project Tool

## Overview

The `webdev_init_project` tool scaffolds production-ready web projects with modern tooling, complete directory structures, and starter code. It provides two preset templates optimized for different use cases.

## Tool Signature

```python
webdev_init_project(
    project_name: str,
    project_title: str,
    description: str,
    features: str,  # "web-static" or "web-db-user"
    framework: str = "react"  # Optional, for web-static preset
)
```

## Parameters

### Required Parameters

- **`project_name`** (string)
  - Project directory name
  - Must contain only alphanumeric characters, hyphens, and underscores
  - Example: `"my-awesome-app"`, `"blog_site"`, `"portfolio2024"`

- **`project_title`** (string)
  - Human-readable project title
  - Used in UI, documentation, and configuration files
  - Example: `"My Awesome App"`, `"Personal Blog"`, `"Portfolio 2024"`

- **`description`** (string)
  - Brief project description
  - Used in package.json, README, and UI components
  - Example: `"A modern web application for managing tasks"`

- **`features`** (string, enum)
  - Project preset type
  - Options:
    - `"web-static"`: Frontend-only static site
    - `"web-db-user"`: Full-stack with backend, database, and authentication

### Optional Parameters

- **`framework`** (string, enum, default: `"react"`)
  - Frontend framework for `web-static` preset
  - Options: `"react"`, `"vue"`
  - Only applicable for `web-static` preset

## Preset Templates

### 1. web-static (Frontend Only)

**Technology Stack:**
- React 18 with Hooks
- Vite (build tool with HMR)
- Tailwind CSS (utility-first styling)
- ESLint (code quality)

**Project Structure:**
```
project-name/
├── public/              # Static assets
├── src/
│   ├── App.jsx          # Main app component
│   ├── main.jsx         # Application entry point
│   └── index.css        # Global styles with Tailwind
├── index.html           # HTML template
├── package.json         # Dependencies and scripts
├── vite.config.js       # Vite configuration
├── tailwind.config.js   # Tailwind configuration
├── postcss.config.js    # PostCSS configuration
├── .gitignore           # Git ignore rules
└── README.md            # Project documentation
```

**Features:**
- Modern React 18 with functional components
- Vite dev server with hot module replacement
- Tailwind CSS with custom configuration
- ESLint setup for code quality
- Production build optimization
- Responsive design examples
- Interactive starter component

**Development Commands:**
```bash
npm install       # Install dependencies
npm run dev       # Start dev server (port 3000)
npm run build     # Build for production
npm run preview   # Preview production build
npm run lint      # Run ESLint
```

### 2. web-db-user (Full-Stack with Auth)

**Technology Stack:**

**Backend:**
- FastAPI (modern Python web framework)
- SQLAlchemy (ORM with async support)
- SQLite (database)
- JWT Authentication (secure token-based auth)
- Pydantic (data validation)
- Bcrypt (password hashing)

**Frontend:**
- React 18 with Hooks
- React Router (client-side routing)
- Axios (HTTP client)
- Vite (build tool)
- Tailwind CSS (styling)

**Project Structure:**
```
project-name/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── auth.py      # Authentication endpoints
│   │   │       └── users.py     # User management
│   │   ├── core/
│   │   │   ├── config.py        # Application settings
│   │   │   └── security.py      # JWT and password utils
│   │   ├── db/
│   │   │   ├── database.py      # Database connection
│   │   │   └── models.py        # SQLAlchemy models
│   │   └── main.py              # FastAPI application
│   ├── requirements.txt         # Python dependencies
│   └── .env.example             # Environment template
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Login.jsx        # Login page
│   │   │   ├── Register.jsx     # Registration page
│   │   │   └── Dashboard.jsx    # Protected dashboard
│   │   ├── App.jsx              # Main app with routing
│   │   ├── main.jsx             # Application entry
│   │   └── index.css            # Global styles
│   ├── package.json             # Dependencies
│   ├── vite.config.js           # Vite with API proxy
│   ├── tailwind.config.js       # Tailwind configuration
│   └── index.html               # HTML template
├── .gitignore                   # Git ignore rules
└── README.md                    # Project documentation
```

**Backend Features:**
- FastAPI with async/await support
- JWT token-based authentication
- User registration and login
- SQLAlchemy ORM with async support
- SQLite database (easy to switch to PostgreSQL/MySQL)
- Password hashing with bcrypt
- CORS middleware configured
- Pydantic models for data validation
- OpenAPI documentation (auto-generated)

**Frontend Features:**
- React Router for navigation
- Login and registration pages
- Protected dashboard route
- JWT token management
- Axios HTTP client with API proxy
- Tailwind CSS styling
- Responsive design
- Form validation

**API Endpoints:**
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user (returns JWT)
- `GET /api/users/me` - Get current user (protected)
- `GET /health` - Health check endpoint
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation

**Development Commands:**

Backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

**Access Points:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Usage Examples

### Example 1: Create Static React Site

```python
result = await webdev_init_project(
    project_name="my-portfolio",
    project_title="John's Portfolio",
    description="Personal portfolio showcasing my projects",
    features="web-static",
    framework="react"
)
```

**Created Project:**
- Location: `/home/ubuntu/my-portfolio/`
- Files: 9 files (package.json, source files, configs, README)
- Ready to: `npm install && npm run dev`

### Example 2: Create Full-Stack App

```python
result = await webdev_init_project(
    project_name="task-manager",
    project_title="Task Manager Pro",
    description="Full-featured task management application",
    features="web-db-user"
)
```

**Created Project:**
- Location: `/home/ubuntu/task-manager/`
- Files: 25+ files (backend API, frontend, configs, README)
- Backend: FastAPI + SQLAlchemy + JWT auth
- Frontend: React + Router + Axios
- Ready to: Set up both backend and frontend separately

## Return Value

The tool returns a `ToolResult` object:

```python
ToolResult(
    success: bool,      # True if project created successfully
    output: str,        # Success message with next steps
    error: str          # Error message if failed (empty on success)
)
```

### Success Response Example

```
✅ Successfully created web-static project: My Portfolio
📁 Location: /home/ubuntu/my-portfolio
📝 Files created: 9

🚀 Next steps:
  cd /home/ubuntu/my-portfolio
  npm install
  npm run dev

📖 The dev server will start at http://localhost:3000
```

### Error Response Example

```
ToolResult(
    success=False,
    output="",
    error="Project name must contain only alphanumeric characters, hyphens, and underscores"
)
```

## File Generation Details

### Common Files (Both Presets)

- **`.gitignore`** - Comprehensive ignore rules for Node, Python, IDEs
- **`README.md`** - Complete project documentation with setup instructions

### web-static Files

1. **`package.json`** - Dependencies (React, Vite, Tailwind, ESLint)
2. **`vite.config.js`** - Vite dev server on port 3000
3. **`tailwind.config.js`** - Tailwind with content paths configured
4. **`postcss.config.js`** - PostCSS with Tailwind and Autoprefixer
5. **`index.html`** - HTML template with root div
6. **`src/main.jsx`** - React 18 rendering with StrictMode
7. **`src/App.jsx`** - Interactive starter component with counter
8. **`src/index.css`** - Tailwind directives and base styles

### web-db-user Files

**Backend (10 files):**
1. **`requirements.txt`** - FastAPI, SQLAlchemy, JWT libraries
2. **`app/main.py`** - FastAPI app with CORS and routes
3. **`app/core/config.py`** - Settings with Pydantic
4. **`app/core/security.py`** - JWT and password hashing
5. **`app/db/database.py`** - Async SQLAlchemy setup
6. **`app/db/models.py`** - User model
7. **`app/api/routes/auth.py`** - Register and login endpoints
8. **`app/api/routes/users.py`** - User management endpoints
9. **`.env.example`** - Environment variable template

**Frontend (10+ files):**
1. **`package.json`** - React, Router, Axios, Vite, Tailwind
2. **`vite.config.js`** - Vite with API proxy to port 8000
3. **`tailwind.config.js`** - Tailwind configuration
4. **`postcss.config.js`** - PostCSS configuration
5. **`index.html`** - HTML template
6. **`src/main.jsx`** - React with Router
7. **`src/App.jsx`** - Main app with routing
8. **`src/pages/Login.jsx`** - Login page with form
9. **`src/pages/Register.jsx`** - Registration page
10. **`src/pages/Dashboard.jsx`** - Protected dashboard
11. **`src/index.css`** - Tailwind and global styles

## Configuration Details

### Vite Configuration

Both presets use Vite with:
- **Host**: `0.0.0.0` (accessible from any network interface)
- **Port**: `3000` (frontend dev server)
- **HMR**: Hot Module Replacement enabled
- **Proxy** (web-db-user): API requests to `http://localhost:8000`

### Tailwind Configuration

- **Content**: Scans all HTML, JS, JSX, TS, TSX files
- **Theme**: Default Tailwind theme with extension support
- **Plugins**: Ready for custom plugin addition

### FastAPI Configuration (web-db-user)

- **CORS**: Configured for localhost:3000 and localhost:5173
- **Database**: SQLite with async support (easily switched to PostgreSQL)
- **JWT**: HS256 algorithm, 30-minute token expiration
- **Security**: Bcrypt password hashing

## Security Considerations

### web-db-user Security Features

1. **Password Hashing**: Bcrypt with automatic salt generation
2. **JWT Tokens**: Secure token-based authentication
3. **CORS**: Restricted to specified origins
4. **Environment Variables**: Sensitive config in .env (not in git)
5. **SQL Injection Prevention**: SQLAlchemy ORM parameterization
6. **Input Validation**: Pydantic models for all endpoints

### Security Best Practices

**Required Actions:**
1. Change `SECRET_KEY` in production (in .env file)
2. Use HTTPS in production
3. Configure proper CORS origins
4. Use environment-specific configurations
5. Implement rate limiting for API endpoints
6. Add input validation and sanitization
7. Set up database backups

## Customization Guide

### Adding Features to web-static

1. **New Component**: Add to `src/components/`
2. **Routing**: Install `react-router-dom`
3. **State Management**: Add Zustand or Redux
4. **API Client**: Add Axios for backend calls

### Extending web-db-user Backend

1. **New Model**: Add to `app/db/models.py`
2. **New Route**: Create file in `app/api/routes/`
3. **Database Migration**: Use Alembic for schema changes
4. **Environment Config**: Add to `app/core/config.py`

### Extending web-db-user Frontend

1. **New Page**: Add to `src/pages/`
2. **New Route**: Update `src/App.jsx`
3. **API Service**: Create `src/services/api.js`
4. **State Management**: Add Context or Zustand

## Troubleshooting

### Common Issues

**Issue: Port already in use**
- Solution: Change port in `vite.config.js` or kill process on port 3000/8000

**Issue: Database connection error**
- Solution: Ensure SQLite file permissions, check database URL in .env

**Issue: CORS errors**
- Solution: Update `CORS_ORIGINS` in `backend/app/core/config.py`

**Issue: JWT token expired**
- Solution: Increase `ACCESS_TOKEN_EXPIRE_MINUTES` or implement refresh tokens

**Issue: npm install fails**
- Solution: Use Node.js 18+ and clear npm cache

## Migration Path

### From web-static to web-db-user

1. Keep existing frontend code
2. Create `backend/` directory with API
3. Update `vite.config.js` to add proxy
4. Add authentication to frontend
5. Connect frontend to new API endpoints

### Database Migration (SQLite to PostgreSQL)

1. Update `DATABASE_URL` in `.env`
2. Install `psycopg2-binary` or `asyncpg`
3. Update SQLAlchemy engine configuration
4. Run database initialization

## Performance Characteristics

### Build Times

- **web-static**: 2-5 seconds for dev build, 10-30 seconds for production
- **web-db-user**: Backend instant start, frontend 2-5 seconds

### Bundle Sizes

- **web-static**: ~150KB initial bundle (gzipped)
- **web-db-user frontend**: ~200KB initial bundle (gzipped)

### Development Experience

- **HMR Speed**: <100ms for file changes
- **Cold Start**: 1-3 seconds for dev server
- **API Response**: <50ms for local backend

## Implementation Details

### File Creation Process

1. Validates project name format
2. Constructs project path at `/home/ubuntu/{project_name}`
3. Generates template files based on preset
4. Creates directory structure as needed
5. Writes all files using sandbox file operations
6. Returns success status with next steps

### Template Generation

- **Static Template**: 9 files, ~500 lines of code
- **Fullstack Template**: 25+ files, ~2000 lines of code
- **Customizable**: Project name, title, description injected into templates

### Error Handling

- Invalid project name: Returns error before file creation
- File write failures: Reports which files failed
- Partial failures: Lists successful and failed files

## Related Tools

- **`file_write`**: Used internally for file creation
- **`file_read`**: Use to inspect generated files
- **`shell_command`**: Use to run npm install, start servers
- **`expose_url`**: Use to expose dev server publicly

## Version History

- **v1.0.0** (2024): Initial implementation
  - React + Vite + Tailwind (web-static)
  - FastAPI + React + Auth (web-db-user)
  - Production-ready configurations

## Future Enhancements

Planned features:
- Vue.js template for web-static
- TypeScript variants
- Next.js preset
- Docker configurations
- CI/CD pipeline templates
- Testing setup (Jest, Pytest)
- Additional database options (PostgreSQL, MongoDB)
