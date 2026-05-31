import time
import sys

print("[startup] Python startup beginning...")

try:
    print("[startup] Importing FastAPI...")
    from fastapi import FastAPI
    print("[startup] FastAPI imported successfully")
except Exception as e:
    print(f"[startup] ERROR importing FastAPI: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("[startup] Importing FastAPI StaticFiles...")
    from fastapi.staticfiles import StaticFiles
    print("[startup] FastAPI StaticFiles imported successfully")
except Exception as e:
    print(f"[startup] ERROR importing StaticFiles: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("[startup] Importing CORSMiddleware...")
    from fastapi.middleware.cors import CORSMiddleware
    print("[startup] CORSMiddleware imported successfully")
except Exception as e:
    print(f"[startup] ERROR importing CORSMiddleware: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("[startup] Importing routers...")
    from routers import (
        alphabet_router,
        words_router,
        translator_router,
        spell_router,
        quiz_router,
        progress_router,
    )
    from auth.auth_router import router as auth_router
    print("[startup] All routers imported successfully")
except Exception as e:
    print(f"[startup] ERROR importing routers: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("[startup] Creating FastAPI app...")
    app = FastAPI(title="SignBridge API", version="1.0.0")
    print("[startup] FastAPI app created successfully")
except Exception as e:
    print(f"[startup] ERROR creating FastAPI app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# CORS middleware
try:
    print("[startup] Adding CORS middleware...")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    print("[startup] CORS middleware added successfully")
except Exception as e:
    print(f"[startup] ERROR adding CORS middleware: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Include routers FIRST (specific routes take precedence)
try:
    print("[startup] Registering routers...")
    app.include_router(alphabet_router.router, prefix="", tags=["alphabet"])
    print("[startup] Alphabet router registered")
    app.include_router(words_router.router, prefix="/api/words", tags=["words"])
    print("[startup] Words router registered")
    app.include_router(translator_router.router, prefix="", tags=["translator"])
    print("[startup] Translator router registered")
    app.include_router(spell_router.router, prefix="", tags=["spell"])
    print("[startup] Spell router registered")
    app.include_router(quiz_router.router, prefix="", tags=["quiz"])
    print("[startup] Quiz router registered")
    app.include_router(progress_router.router, prefix="", tags=["progress"])
    print("[startup] Progress router registered")
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    print("[startup] Auth router registered")
    print("[startup] All routers registered successfully")
except Exception as e:
    print(f"[startup] ERROR registering routers: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Ensure auth DB tables are created so SQLite tables (e.g. users) exist
try:
    print("[startup] Ensuring database tables exist...")
    import auth.database as _database
    import auth.models as _models  # registers models with Base
    _database.Base.metadata.create_all(bind=_database.engine)
    # If an older `users` table schema exists, attempt to add missing columns
    from sqlalchemy import inspect, text
    inspector = inspect(_database.engine)
    if 'users' in inspector.get_table_names():
        existing_cols = {col['name'] for col in inspector.get_columns('users')}
        # expected columns set
        expected_cols = {'id', 'first_name', 'last_name', 'email', 'hashed_password', 'created_at', 'is_verified', 'verification_code', 'verification_expires'}
        missing = expected_cols - existing_cols
        if missing:
            print(f'[startup] Detected missing users columns: {missing}; attempting to ALTER TABLE to add them')
            with _database.engine.connect() as conn:
                for col in missing:
                    try:
                        if col == 'is_verified':
                            conn.execute(text("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT 0"))
                        elif col == 'verification_code':
                            conn.execute(text("ALTER TABLE users ADD COLUMN verification_code VARCHAR(128)"))
                        elif col == 'verification_expires':
                            conn.execute(text("ALTER TABLE users ADD COLUMN verification_expires DATETIME"))
                        else:
                            print(f'[startup] Unexpected missing column: {col}')
                    except Exception as e:
                        print(f'[startup] Could not add column {col}: {e}')
    print("[startup] Database tables ready")
except Exception as e:
    print(f"[startup] ERROR creating database tables: {e}")
    import traceback
    traceback.print_exc()
    # Do not exit; allow app to start but table ops will fail until resolved

# Mount static files LAST (catch-all for everything else)
try:
    print("[startup] Mounting static files...")
    app.mount("/", StaticFiles(directory=".", html=True), name="static")
    print("[startup] Static files mounted successfully")
except Exception as e:
    print(f"[startup] ERROR mounting static files: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("[startup] All initialization complete. Ready to start uvicorn.")

if __name__ == "__main__":
    import sys
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False if sys.platform == "win32" else True,
    )