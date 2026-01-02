from typing import Optional, Dict, Any, List
from app.domain.external.sandbox import Sandbox
from app.domain.services.tools.base import tool, BaseTool
from app.domain.models.tool_result import ToolResult
import os


class WebDevTool(BaseTool):
    """Web development tool for project scaffolding and initialization"""

    name: str = "webdev"

    def __init__(self, sandbox: Sandbox):
        """Initialize web development tool

        Args:
            sandbox: Sandbox service for file operations
        """
        super().__init__()
        self.sandbox = sandbox
        self.base_path = "/home/ubuntu"

    def _get_static_template(self, project_name: str, project_title: str, description: str, framework: str = "react") -> Dict[str, str]:
        """Get static web project template files

        Args:
            project_name: Project directory name
            project_title: Human-readable project title
            description: Project description
            framework: Frontend framework (react or vue)

        Returns:
            Dictionary of file paths to contents
        """
        files = {}

        if framework == "react":
            # package.json
            files["package.json"] = f'''{{
  "name": "{project_name}",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "description": "{description}",
  "scripts": {{
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext js,jsx --report-unused-disable-directives --max-warnings 0"
  }},
  "dependencies": {{
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  }},
  "devDependencies": {{
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "autoprefixer": "^10.4.19",
    "eslint": "^8.57.0",
    "eslint-plugin-react": "^7.34.2",
    "eslint-plugin-react-hooks": "^4.6.2",
    "eslint-plugin-react-refresh": "^0.4.7",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.4",
    "vite": "^5.3.1"
  }}
}}
'''

            # vite.config.js
            files["vite.config.js"] = '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000
  }
})
'''

            # tailwind.config.js
            files["tailwind.config.js"] = '''/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
'''

            # postcss.config.js
            files["postcss.config.js"] = '''export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
'''

            # index.html
            files["index.html"] = f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{project_title}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
'''

            # src/main.jsx
            files["src/main.jsx"] = '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
'''

            # src/App.jsx
            files["src/App.jsx"] = f'''import {{ useState }} from 'react'

function App() {{
  const [count, setCount] = useState(0)

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-400 via-pink-500 to-red-500 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-2xl p-8 max-w-md w-full">
        <h1 className="text-4xl font-bold text-gray-800 mb-4 text-center">
          {project_title}
        </h1>
        <p className="text-gray-600 mb-8 text-center">
          {description}
        </p>

        <div className="bg-gray-100 rounded-lg p-6 mb-6">
          <p className="text-6xl font-bold text-center text-purple-600 mb-4">
            {{count}}
          </p>
          <button
            onClick={{() => setCount(count + 1)}}
            className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-4 rounded-lg transition duration-200"
          >
            Click me!
          </button>
        </div>

        <div className="text-center text-sm text-gray-500">
          <p>Edit <code className="bg-gray-200 px-2 py-1 rounded">src/App.jsx</code> to get started</p>
        </div>
      </div>
    </div>
  )
}}

export default App
'''

            # src/index.css
            files["src/index.css"] = '''@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
  line-height: 1.5;
  font-weight: 400;
}

body {
  margin: 0;
  padding: 0;
}
'''

            # .gitignore
            files[".gitignore"] = '''# Dependencies
node_modules
.pnp
.pnp.js

# Testing
coverage

# Production
dist
build

# Misc
.DS_Store
.env.local
.env.development.local
.env.test.local
.env.production.local

# Logs
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*

# Editor
.vscode
.idea
*.swp
*.swo
*~
'''

            # README.md
            files["README.md"] = f'''# {project_title}

{description}

## Getting Started

### Prerequisites

- Node.js (v18 or higher)
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Features

- ⚡️ Vite - Lightning fast HMR
- ⚛️ React 18 - Latest React features
- 🎨 Tailwind CSS - Utility-first CSS framework
- 📦 Production-ready build configuration

## Project Structure

```
{project_name}/
├── public/          # Static assets
├── src/
│   ├── App.jsx      # Main app component
│   ├── main.jsx     # App entry point
│   └── index.css    # Global styles
├── index.html       # HTML template
├── package.json     # Dependencies
├── vite.config.js   # Vite configuration
└── tailwind.config.js # Tailwind configuration
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## License

MIT
'''

        return files

    def _get_fullstack_template(self, project_name: str, project_title: str, description: str) -> Dict[str, str]:
        """Get full-stack web project template files

        Args:
            project_name: Project directory name
            project_title: Human-readable project title
            description: Project description

        Returns:
            Dictionary of file paths to contents
        """
        files = {}

        # Backend files
        # requirements.txt
        files["backend/requirements.txt"] = '''fastapi==0.111.0
uvicorn[standard]==0.30.1
python-dotenv==1.0.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
sqlalchemy==2.0.30
aiosqlite==0.20.0
pydantic==2.7.4
pydantic-settings==2.3.3
'''

        # backend/app/main.py
        files["backend/app/main.py"] = f'''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import auth, users
from app.core.config import settings
from app.db.database import init_db

app = FastAPI(
    title="{project_title} API",
    description="{description}",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await init_db()

@app.get("/")
async def root():
    """Root endpoint"""
    return {{"message": "Welcome to {project_title} API"}}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {{"status": "healthy"}}
'''

        # backend/app/core/config.py
        files["backend/app/core/config.py"] = '''from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """Application settings"""

    # API Settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Web App"

    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
'''

        # backend/app/core/security.py
        files["backend/app/core/security.py"] = '''from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
'''

        # backend/app/db/database.py
        files["backend/app/db/database.py"] = '''from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    """Get database session"""
    async with async_session() as session:
        yield session
'''

        # backend/app/db/models.py
        files["backend/app/db/models.py"] = '''from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.db.database import Base

class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
'''

        # backend/app/api/routes/auth.py
        files["backend/app/api/routes/auth.py"] = '''from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.db.models import User
from app.core.security import verify_password, get_password_hash, create_access_token
from pydantic import BaseModel, EmailStr

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/register", response_model=Token)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register new user"""
    # Check if user exists
    result = await db.execute(select(User).where(User.email == user.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=get_password_hash(user.password)
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    # Create access token
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Login user"""
    # Get user
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}
'''

        # backend/app/api/routes/users.py
        files["backend/app/api/routes/users.py"] = '''from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.db.models import User
from pydantic import BaseModel

router = APIRouter()

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool

@router.get("/me", response_model=UserResponse)
async def get_current_user(db: AsyncSession = Depends(get_db)):
    """Get current user"""
    # Simplified - in production, get user from JWT token
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    return user
'''

        # backend/.env.example
        files["backend/.env.example"] = '''SECRET_KEY=your-secret-key-change-this-in-production
DATABASE_URL=sqlite+aiosqlite:///./app.db
'''

        # Frontend files (React + Vite)
        # frontend/package.json
        files["frontend/package.json"] = f'''{{
  "name": "{project_name}-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {{
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  }},
  "dependencies": {{
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.23.1",
    "axios": "^1.7.2"
  }},
  "devDependencies": {{
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.4",
    "vite": "^5.3.1"
  }}
}}
'''

        # frontend/vite.config.js
        files["frontend/vite.config.js"] = '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
'''

        # frontend/tailwind.config.js
        files["frontend/tailwind.config.js"] = '''/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
'''

        # frontend/postcss.config.js
        files["frontend/postcss.config.js"] = '''export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
'''

        # frontend/index.html
        files["frontend/index.html"] = f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{project_title}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
'''

        # frontend/src/main.jsx
        files["frontend/src/main.jsx"] = '''import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)
'''

        # frontend/src/App.jsx
        files["frontend/src/App.jsx"] = f'''import {{ useState }} from 'react'
import {{ Routes, Route }} from 'react-router-dom'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'

function App() {{
  return (
    <div className="min-h-screen bg-gray-50">
      <Routes>
        <Route path="/login" element={{<Login />}} />
        <Route path="/register" element={{<Register />}} />
        <Route path="/" element={{<Dashboard />}} />
      </Routes>
    </div>
  )
}}

export default App
'''

        # frontend/src/pages/Login.jsx
        files["frontend/src/pages/Login.jsx"] = f'''import {{ useState }} from 'react'
import {{ useNavigate, Link }} from 'react-router-dom'
import axios from 'axios'

function Login() {{
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleSubmit = async (e) => {{
    e.preventDefault()
    setError('')

    try {{
      const formData = new FormData()
      formData.append('username', email)
      formData.append('password', password)

      const response = await axios.post('/api/auth/login', formData)
      localStorage.setItem('token', response.data.access_token)
      navigate('/')
    }} catch (err) {{
      setError(err.response?.data?.detail || 'Login failed')
    }}
  }}

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-400 to-purple-500">
      <div className="bg-white p-8 rounded-lg shadow-2xl w-full max-w-md">
        <h1 className="text-3xl font-bold text-center mb-8 text-gray-800">{project_title}</h1>
        <h2 className="text-xl font-semibold text-center mb-6 text-gray-600">Login</h2>

        {{error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {{error}}
          </div>
        )}}

        <form onSubmit={{handleSubmit}} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
            <input
              type="email"
              value={{email}}
              onChange={{(e) => setEmail(e.target.value)}}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
            <input
              type="password"
              value={{password}}
              onChange={{(e) => setPassword(e.target.value)}}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          <button
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg transition duration-200"
          >
            Login
          </button>
        </form>

        <p className="text-center mt-6 text-gray-600">
          Don't have an account?{{' '}}
          <Link to="/register" className="text-blue-600 hover:text-blue-700 font-semibold">
            Register
          </Link>
        </p>
      </div>
    </div>
  )
}}

export default Login
'''

        # frontend/src/pages/Register.jsx
        files["frontend/src/pages/Register.jsx"] = f'''import {{ useState }} from 'react'
import {{ useNavigate, Link }} from 'react-router-dom'
import axios from 'axios'

function Register() {{
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleSubmit = async (e) => {{
    e.preventDefault()
    setError('')

    try {{
      const response = await axios.post('/api/auth/register', {{
        email,
        username,
        password
      }})
      localStorage.setItem('token', response.data.access_token)
      navigate('/')
    }} catch (err) {{
      setError(err.response?.data?.detail || 'Registration failed')
    }}
  }}

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-400 to-pink-500">
      <div className="bg-white p-8 rounded-lg shadow-2xl w-full max-w-md">
        <h1 className="text-3xl font-bold text-center mb-8 text-gray-800">{project_title}</h1>
        <h2 className="text-xl font-semibold text-center mb-6 text-gray-600">Create Account</h2>

        {{error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {{error}}
          </div>
        )}}

        <form onSubmit={{handleSubmit}} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
            <input
              type="email"
              value={{email}}
              onChange={{(e) => setEmail(e.target.value)}}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Username</label>
            <input
              type="text"
              value={{username}}
              onChange={{(e) => setUsername(e.target.value)}}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
            <input
              type="password"
              value={{password}}
              onChange={{(e) => setPassword(e.target.value)}}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              required
            />
          </div>

          <button
            type="submit"
            className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-4 rounded-lg transition duration-200"
          >
            Register
          </button>
        </form>

        <p className="text-center mt-6 text-gray-600">
          Already have an account?{{' '}}
          <Link to="/login" className="text-purple-600 hover:text-purple-700 font-semibold">
            Login
          </Link>
        </p>
      </div>
    </div>
  )
}}

export default Register
'''

        # frontend/src/pages/Dashboard.jsx
        files["frontend/src/pages/Dashboard.jsx"] = f'''import {{ useState, useEffect }} from 'react'
import {{ useNavigate }} from 'react-router-dom'
import axios from 'axios'

function Dashboard() {{
  const [user, setUser] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {{
    const token = localStorage.getItem('token')
    if (!token) {{
      navigate('/login')
      return
    }}

    // Fetch user data
    axios.get('/api/users/me', {{
      headers: {{ Authorization: `Bearer ${{token}}` }}
    }})
    .then(response => setUser(response.data))
    .catch(() => {{
      localStorage.removeItem('token')
      navigate('/login')
    }})
  }}, [navigate])

  const handleLogout = () => {{
    localStorage.removeItem('token')
    navigate('/login')
  }}

  if (!user) {{
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-600">Loading...</div>
      </div>
    )
  }}

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-800">{project_title}</h1>
            </div>
            <div className="flex items-center">
              <span className="text-gray-600 mr-4">{{user.username}}</span>
              <button
                onClick={{handleLogout}}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition duration-200"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Welcome, {{user.username}}!</h2>
          <p className="text-gray-600 mb-4">
            You're logged in to {project_title}. This is your dashboard.
          </p>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-semibold text-blue-800 mb-2">User Information</h3>
            <p className="text-blue-700">Email: {{user.email}}</p>
            <p className="text-blue-700">Username: {{user.username}}</p>
            <p className="text-blue-700">Status: {{user.is_active ? 'Active' : 'Inactive'}}</p>
          </div>
        </div>
      </main>
    </div>
  )
}}

export default Dashboard
'''

        # frontend/src/index.css
        files["frontend/src/index.css"] = '''@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
  line-height: 1.5;
  font-weight: 400;
}

body {
  margin: 0;
  padding: 0;
}
'''

        # Root .gitignore
        files[".gitignore"] = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv
*.egg-info/
dist/
build/

# JavaScript
node_modules/
.pnp
.pnp.js
dist/
build/

# Database
*.db
*.sqlite
*.sqlite3

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
'''

        # Root README.md
        files["README.md"] = f'''# {project_title}

{description}

## Project Structure

```
{project_name}/
├── backend/          # FastAPI backend
│   ├── app/
│   │   ├── api/      # API routes
│   │   ├── core/     # Core configuration
│   │   └── db/       # Database models
│   └── requirements.txt
├── frontend/         # React frontend
│   ├── src/
│   │   ├── pages/    # Page components
│   │   └── App.jsx
│   └── package.json
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Run backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at: http://localhost:3000

## Features

### Backend
- ⚡️ FastAPI - Modern, fast web framework
- 🔐 JWT Authentication - Secure user authentication
- 🗃️ SQLAlchemy - SQL toolkit and ORM
- 🔄 Async/Await - Asynchronous database operations
- 📝 Pydantic - Data validation

### Frontend
- ⚛️ React 18 - Latest React features
- 🎨 Tailwind CSS - Utility-first CSS framework
- 🛣️ React Router - Client-side routing
- 📡 Axios - HTTP client
- ⚡️ Vite - Lightning fast HMR

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Available Endpoints

### Authentication
- POST `/api/auth/register` - Register new user
- POST `/api/auth/login` - Login user

### Users
- GET `/api/users/me` - Get current user

## Development

### Backend Development
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
npm run dev
```

## Production Build

### Backend
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm run build
npm run preview
```

## License

MIT
'''

        return files

    @tool(
        name="webdev_init_project",
        description="Initialize a web project with production-ready template. Creates complete project structure with modern tooling, dependencies, and starter code.",
        parameters={
            "project_name": {
                "type": "string",
                "description": "Project directory name (lowercase, hyphens allowed)"
            },
            "project_title": {
                "type": "string",
                "description": "Human-readable project title"
            },
            "description": {
                "type": "string",
                "description": "Project description"
            },
            "features": {
                "type": "string",
                "enum": ["web-static", "web-db-user"],
                "description": "Project preset: 'web-static' for frontend-only (React+Vite+Tailwind), 'web-db-user' for full-stack (FastAPI+React+SQLite+Auth)"
            },
            "framework": {
                "type": "string",
                "enum": ["react", "vue"],
                "description": "(Optional) Frontend framework for web-static preset. Default: react"
            }
        },
        required=["project_name", "project_title", "description", "features"]
    )
    async def init_project(
        self,
        project_name: str,
        project_title: str,
        description: str,
        features: str,
        framework: Optional[str] = "react"
    ) -> ToolResult:
        """Initialize web project with production-ready template

        Args:
            project_name: Project directory name
            project_title: Human-readable project title
            description: Project description
            features: Project preset (web-static or web-db-user)
            framework: Frontend framework (react or vue) for web-static

        Returns:
            ToolResult with created project information
        """
        try:
            # Validate project name
            if not project_name.replace('-', '').replace('_', '').isalnum():
                return ToolResult(
                    success=False,
                    output="",
                    error="Project name must contain only alphanumeric characters, hyphens, and underscores"
                )

            # Construct project path
            project_path = os.path.join(self.base_path, project_name)

            # Get template files based on preset
            if features == "web-static":
                files = self._get_static_template(project_name, project_title, description, framework)
            elif features == "web-db-user":
                files = self._get_fullstack_template(project_name, project_title, description)
            else:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Unknown preset: {features}. Use 'web-static' or 'web-db-user'"
                )

            # Create all files
            created_files = []
            failed_files = []

            for file_path, content in files.items():
                full_path = os.path.join(project_path, file_path)

                # Create directories if they don't exist
                file_dir = os.path.dirname(full_path)
                if file_dir:
                    # Create directory structure
                    dir_parts = file_dir.replace(project_path, '').strip('/').split('/')
                    current_dir = project_path
                    for part in dir_parts:
                        if part:
                            current_dir = os.path.join(current_dir, part)

                # Write file content
                result = await self.sandbox.file_write(
                    file=full_path,
                    content=content,
                    append=False,
                    sudo=False
                )

                if result.success:
                    created_files.append(file_path)
                else:
                    failed_files.append(f"{file_path}: {result.error}")

            # Generate summary
            if failed_files:
                error_msg = "Some files failed to create:\n" + "\n".join(failed_files)
                return ToolResult(
                    success=False,
                    output=f"Created {len(created_files)} files in {project_path}",
                    error=error_msg
                )

            # Build success message
            output_lines = [
                f"✅ Successfully created {features} project: {project_title}",
                f"📁 Location: {project_path}",
                f"📝 Files created: {len(created_files)}",
                "",
                "🚀 Next steps:"
            ]

            if features == "web-static":
                output_lines.extend([
                    f"  cd {project_path}",
                    "  npm install",
                    "  npm run dev",
                    "",
                    "📖 The dev server will start at http://localhost:3000"
                ])
            elif features == "web-db-user":
                output_lines.extend([
                    "",
                    "Backend:",
                    f"  cd {project_path}/backend",
                    "  python -m venv venv",
                    "  source venv/bin/activate",
                    "  pip install -r requirements.txt",
                    "  cp .env.example .env",
                    "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000",
                    "",
                    "Frontend:",
                    f"  cd {project_path}/frontend",
                    "  npm install",
                    "  npm run dev",
                    "",
                    "📖 Backend: http://localhost:8000",
                    "📖 Frontend: http://localhost:3000",
                    "📖 API Docs: http://localhost:8000/docs"
                ])

            return ToolResult(
                success=True,
                output="\n".join(output_lines),
                error=""
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to initialize project: {str(e)}"
            )
