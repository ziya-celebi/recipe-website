import json
import os
from pathlib import Path
from threading import Lock

from models import Recipe, RecipeCreate

_lock = Lock()
_recipes: list[Recipe] | None = None

SEED_RECIPES: list[Recipe] = []


def data_dir() -> Path:
    # Use /tmp for serverless environments (Vercel), local data directory otherwise
    if os.environ.get("VERCEL"):
        return Path("/tmp/recipe_data")
    return Path(os.environ.get("RECIPE_DATA_DIR", Path(__file__).resolve().parent / "data"))


def recipes_path() -> Path:
    return data_dir() / "recipes.json"


def uploads_dir() -> Path:
    path = data_dir() / "uploads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def reset() -> None:
    global _recipes
    with _lock:
        _recipes = None


def _read_file() -> list[Recipe] | None:
    path = recipes_path()
    if not path.exists():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [Recipe.model_validate(item) for item in raw]


def _write_file(recipes: list[Recipe]) -> None:
    path = recipes_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([recipe.model_dump() for recipe in recipes], indent=2) + "\n",
        encoding="utf-8",
    )


def _loaded() -> list[Recipe]:
    global _recipes
    if _recipes is None:
        _recipes = _read_file()
        if _recipes is None:
            _recipes = [recipe.model_copy() for recipe in SEED_RECIPES]
            _write_file(_recipes)
    return _recipes


def list_recipes() -> list[Recipe]:
    with _lock:
        return [recipe.model_copy() for recipe in _loaded()]


def get_recipe(recipe_id: int) -> Recipe | None:
    with _lock:
        for recipe in _loaded():
            if recipe.id == recipe_id:
                return recipe.model_copy()
    return None


def create_recipe(payload: RecipeCreate) -> Recipe:
    with _lock:
        recipes = _loaded()
        next_id = max((recipe.id for recipe in recipes), default=0) + 1
        recipe = Recipe(id=next_id, **payload.model_dump())
        recipes.append(recipe)
        _write_file(recipes)
        return recipe.model_copy()


def delete_recipe(recipe_id: int) -> bool:
    with _lock:
        recipes = _loaded()
        for i, recipe in enumerate(recipes):
            if recipe.id == recipe_id:
                recipes.pop(i)
                _write_file(recipes)
                return True
        return False
