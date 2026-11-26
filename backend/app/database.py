import os

from sqlmodel import Session, SQLModel, create_engine, select

from .config import settings

# FastAPI may use a SQLite connection across worker threads; this setting is SQLite-specific.
_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=_connect_args)


def get_session():
    # expire_on_commit=False keeps ORM objects readable for response serialization after commit
    with Session(engine, expire_on_commit=False) as session:
        yield session


def init_db() -> None:
    if settings.database_url.startswith("sqlite:///./"):
        os.makedirs("data", exist_ok=True)
    SQLModel.metadata.create_all(engine)
    _seed()


def _seed() -> None:
    from datetime import datetime, timezone

    from .models import Organization, User, UserRole
    from .security import hash_password

    with Session(engine) as session:
        # Seed only an empty user table; startup does not reset existing users or passwords.
        if session.exec(select(User)).first():
            return
        now = datetime.now(timezone.utc)
        org = Organization(name="Demo Corp", created_at=now, updated_at=now)
        session.add(org)
        session.commit()
        session.refresh(org)
        session.add_all(
            [
                User(
                    email="admin@demo.com",
                    password_hash=hash_password("Password123!"),
                    first_name="System",
                    last_name="Admin",
                    role=UserRole.SYSTEM_ADMIN.value,
                    organization_id=org.id,
                    enabled=True,
                    created_at=now,
                    updated_at=now,
                ),
                User(
                    email="hr@demo.com",
                    password_hash=hash_password("Password123!"),
                    first_name="HR",
                    last_name="User",
                    role=UserRole.CLIENT_USER.value,
                    organization_id=org.id,
                    enabled=True,
                    created_at=now,
                    updated_at=now,
                ),
            ]
        )
        session.commit()
