from typing import Optional
from fastapi import FastAPI
from contextlib import asynccontextmanager
import os
import subprocess
from pathlib import Path

class ServiceDatabase:
    def __init__(self, service_name: str):
        self.service_name = service_name
    
    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """FastAPI lifespan context manager"""
        # Startup
        from shared.database.connection import get_database_url, db
        
        database_url = get_database_url()
        await db.connect(database_url)
        
        # Run migrations if enabled (only run from unified migrations)
        if os.getenv("RUN_MIGRATIONS", "false").lower() == "true":
            print(f"Running unified database migrations for {self.service_name}...")
            self._run_unified_migrations()
        
        print(f"✓ {self.service_name} database connected")
        
        yield
        
        # Shutdown
        await db.disconnect()
        print(f"✓ {self.service_name} database disconnected")
    
    def _run_unified_migrations(self):
        """Run migrations from central database_migrations folder"""
        try:
            migrations_dir = Path("database_migrations")
            if migrations_dir.exists():
                result = subprocess.run(
                    ["poetry", "run", "alembic", "upgrade", "head"],
                    cwd=migrations_dir,
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print("✅ Unified migrations completed successfully")
                else:
                    print(f"❌ Migration failed: {result.stderr}")
            else:
                print("⚠️ No unified migrations directory found")
        except Exception as e:
            print(f"❌ Error running unified migrations: {e}")