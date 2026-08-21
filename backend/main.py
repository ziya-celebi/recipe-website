from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from admin import router as admin_router
from models import Recipe, RecipeCreate
from store import (
    create_recipe,
    delete_recipe,
    get_recipe as store_get_recipe,
    list_recipes as store_list_recipes,
    uploads_dir,
)

app = FastAPI(title="Recipe API", description="API and Admin Panel for Recipes")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.mount("/media", StaticFiles(directory=str(uploads_dir())), name="media")

app.include_router(admin_router)


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI!"}


@app.get("/recipes", response_model=list[Recipe])
def list_recipes(q: str | None = None):
    recipes = store_list_recipes()
    if not q:
        return recipes
    query = q.strip().lower()
    return [
        recipe
        for recipe in recipes
        if query in recipe.title.lower()
        or query in recipe.description.lower()
        or any(query in ingredient.lower() for ingredient in recipe.ingredients)
    ]


@app.get("/recipes/{recipe_id}", response_model=Recipe)
def get_recipe(recipe_id: int):
    recipe = store_get_recipe(recipe_id)
    if recipe is not None:
        return recipe
    raise HTTPException(status_code=404, detail="Recipe not found")


@app.post("/recipes", response_model=Recipe, status_code=status.HTTP_201_CREATED)
def add_recipe(payload: RecipeCreate):
    if not payload.title.strip():
        raise HTTPException(status_code=400, detail="Recipe title is required")
    return create_recipe(payload)


@app.delete("/recipes/{recipe_id}")
def remove_recipe(recipe_id: int):
    deleted = delete_recipe(recipe_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return {"message": "Recipe deleted successfully", "id": recipe_id}
