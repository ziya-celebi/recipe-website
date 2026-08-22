import json
import os
from pathlib import Path
from threading import Lock

from sqlalchemy import (
    Column,
    Integer,
    LargeBinary,
    String,
    Text,
    JSON,
    create_engine,
    select,
    delete,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from models import Recipe, RecipeCreate

_lock = Lock()
_engine = None
_SessionLocal = None

SEED_RECIPES: list[Recipe] = []

Base = declarative_base()


class RecipeRecord(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False, default="")
    image = Column(Text, nullable=True)
    ingredients = Column(JSON, nullable=False, default=list)
    steps = Column(JSON, nullable=False, default=list)

    def to_pydantic(self) -> Recipe:
        return Recipe(
            id=self.id,
            title=self.title,
            description=self.description or "",
            image=self.image,
            ingredients=list(self.ingredients or []),
            steps=list(self.steps or []),
        )


class ImageRecord(Base):
    __tablename__ = "recipe_images"

    filename = Column(String(255), primary_key=True)
    content_type = Column(String(100), nullable=False, default="application/octet-stream")
    data = Column(LargeBinary, nullable=False)


def data_dir() -> Path:
    # Use /tmp for serverless environments (Vercel), local data directory otherwise
    if os.environ.get("VERCEL"):
        return Path("/tmp/recipe_data")
    return Path(os.environ.get("RECIPE_DATA_DIR", Path(__file__).resolve().parent / "data"))


def uploads_dir() -> Path:
    path = data_dir() / "uploads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_db_url() -> str:
    url = (
        os.environ.get("DATABASE_URL")
        or os.environ.get("POSTGRES_URL")
        or os.environ.get("POSTGRES_PRISMA_URL")
    )
    if url:
        # SQLAlchemy requires postgresql:// instead of postgres://
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url

    # Default to local SQLite database
    db_dir = data_dir()
    db_dir.mkdir(parents=True, exist_ok=True)
    db_file = db_dir / "recipes.db"
    return f"sqlite:///{db_file}"


def is_postgres() -> bool:
    return get_db_url().startswith("postgresql")


def get_db_type() -> str:
    return "PostgreSQL (Cloud)" if is_postgres() else "SQLite (Local)"


def _get_session_factory():
    global _engine, _SessionLocal
    if _SessionLocal is None:
        db_url = get_db_url()
        connect_args = {}
        engine_kwargs = {"pool_pre_ping": True}
        if db_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
            # SQLite doesn't support pool_pre_ping
            engine_kwargs.pop("pool_pre_ping", None)

        _engine = create_engine(db_url, connect_args=connect_args, **engine_kwargs)
        Base.metadata.create_all(bind=_engine)
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

        # Seed initial data if table is brand new and empty
        _maybe_seed(_SessionLocal)

    return _SessionLocal


def _maybe_seed(session_factory):
    with session_factory() as session:
        count = session.query(RecipeRecord).count()
        if count == 0:
            # 1. Seed from SEED_RECIPES if defined
            if SEED_RECIPES:
                for recipe in SEED_RECIPES:
                    record = RecipeRecord(
                        title=recipe.title,
                        description=recipe.description,
                        image=recipe.image,
                        ingredients=recipe.ingredients,
                        steps=recipe.steps,
                    )
                    session.add(record)
                session.commit()
            else:
                # 2. Check if an existing legacy recipes.json exists to migrate
                json_path = data_dir() / "recipes.json"
                if json_path.exists():
                    try:
                        raw = json.loads(json_path.read_text(encoding="utf-8"))
                        for item in raw:
                            record = RecipeRecord(
                                title=item.get("title", ""),
                                description=item.get("description", ""),
                                image=item.get("image"),
                                ingredients=item.get("ingredients", []),
                                steps=item.get("steps", []),
                            )
                            session.add(record)
                        session.commit()
                    except Exception:
                        pass


def reset() -> None:
    global _engine, _SessionLocal
    with _lock:
        if _engine is not None:
            _engine.dispose()
        _engine = None
        _SessionLocal = None


def list_recipes() -> list[Recipe]:
    with _lock:
        session_factory = _get_session_factory()
        with session_factory() as session:
            records = session.query(RecipeRecord).order_by(RecipeRecord.id.asc()).all()
            return [record.to_pydantic() for record in records]


def get_recipe(recipe_id: int) -> Recipe | None:
    with _lock:
        session_factory = _get_session_factory()
        with session_factory() as session:
            record = session.query(RecipeRecord).filter(RecipeRecord.id == recipe_id).first()
            return record.to_pydantic() if record else None


def create_recipe(payload: RecipeCreate) -> Recipe:
    with _lock:
        session_factory = _get_session_factory()
        with session_factory() as session:
            record = RecipeRecord(
                title=payload.title,
                description=payload.description,
                image=payload.image,
                ingredients=payload.ingredients,
                steps=payload.steps,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record.to_pydantic()


def save_image(filename: str, content_type: str, data: bytes) -> None:
    with _lock:
        session_factory = _get_session_factory()
        with session_factory() as session:
            session.add(
                ImageRecord(filename=filename, content_type=content_type, data=data)
            )
            session.commit()


def get_image(filename: str) -> tuple[str, bytes] | None:
    with _lock:
        session_factory = _get_session_factory()
        with session_factory() as session:
            record = session.get(ImageRecord, filename)
            if record is None:
                return None
            return record.content_type, record.data


def delete_recipe(recipe_id: int) -> bool:
    with _lock:
        session_factory = _get_session_factory()
        with session_factory() as session:
            record = session.query(RecipeRecord).filter(RecipeRecord.id == recipe_id).first()
            if record:
                session.delete(record)
                session.commit()
                return True
            return False

