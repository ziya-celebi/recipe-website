import json
import os
from pathlib import Path
from threading import Lock

from models import Recipe, RecipeCreate

_lock = Lock()
_recipes: list[Recipe] | None = None

SEED_RECIPES = [
    Recipe(
        id=1,
        title="Pancakes",
        description="Fluffy breakfast pancakes with a golden crust.",
        image=None,
        ingredients=[
            "1 cup flour",
            "1 cup milk",
            "1 egg",
            "1 tbsp sugar",
            "1 tsp baking powder",
            "pinch of salt",
        ],
        steps=[
            "Whisk the dry ingredients together.",
            "Stir in milk and egg until just combined.",
            "Cook scoops on a buttered pan until both sides are golden.",
        ],
    ),
    Recipe(
        id=2,
        title="Tomato Pasta",
        description="A simple weeknight pasta with a garlicky tomato sauce.",
        image=None,
        ingredients=[
            "200g pasta",
            "1 can crushed tomatoes",
            "2 garlic cloves",
            "olive oil",
            "salt and pepper",
        ],
        steps=[
            "Boil the pasta in salted water.",
            "Sauté garlic in olive oil, then add tomatoes.",
            "Toss the drained pasta with the sauce and season.",
        ],
    ),
    Recipe(
        id=3,
        title="Avocado Toast with Poached Egg",
        description="Crispy sourdough toast topped with creamy crushed avocado, a runny poached egg, and red pepper flakes.",
        image=None,
        ingredients=[
            "2 thick slices sourdough bread",
            "1 ripe avocado",
            "2 fresh eggs",
            "1 tbsp fresh lemon juice",
            "1 tbsp extra virgin olive oil",
            "Pinch of red pepper flakes",
            "Flaky sea salt and freshly cracked black pepper",
        ],
        steps=[
            "Toast the sourdough bread slices until golden and crisp.",
            "Mash the avocado in a bowl with lemon juice, salt, and black pepper.",
            "Bring a small pot of water with a dash of vinegar to a gentle simmer, swirl to create a vortex, and poach the eggs for 3 minutes.",
            "Spread the mashed avocado over warm toast, top each slice with a poached egg, drizzle with olive oil, and finish with chili flakes and flaky salt.",
        ],
    ),
    Recipe(
        id=4,
        title="Classic Guacamole & Tortilla Chips",
        description="Fresh and zesty homemade guacamole with ripe avocados, lime juice, cilantro, and diced red onion.",
        image=None,
        ingredients=[
            "3 ripe Haas avocados",
            "1 lime, freshly juiced",
            "1/2 cup diced red onion",
            "1 Roma tomato, seeded and diced",
            "1/4 cup finely chopped cilantro",
            "1 jalapeño, seeded and finely minced",
            "1/2 tsp kosher salt",
            "Crispy tortilla chips for serving",
        ],
        steps=[
            "Cut avocados in half, remove pits, and scoop the flesh into a medium bowl.",
            "Coarsely mash with a fork to your desired chunkiness.",
            "Gently fold in lime juice, red onion, tomato, cilantro, jalapeño, and salt.",
            "Taste and adjust seasoning, then serve immediately with crispy tortilla chips.",
        ],
    ),
    Recipe(
        id=5,
        title="Garlic Butter Sautéed Shrimp",
        description="Plump, juicy shrimp tossed in a rich garlic butter sauce with lemon and fresh parsley in under 15 minutes.",
        image=None,
        ingredients=[
            "400g large shrimp, peeled and deveined",
            "4 cloves garlic, finely minced",
            "3 tbsp unsalted butter",
            "1 tbsp olive oil",
            "2 tbsp freshly squeezed lemon juice",
            "2 tbsp chopped fresh flat-leaf parsley",
            "Salt and freshly cracked black pepper",
        ],
        steps=[
            "Pat the shrimp dry with paper towels and season with salt and pepper.",
            "Heat olive oil and 1 tbsp butter in a large skillet over medium-high heat.",
            "Add shrimp in a single layer and sear for 1-2 minutes per side until pink and opaque.",
            "Reduce heat, add minced garlic and cook for 30 seconds until fragrant.",
            "Stir in remaining butter and lemon juice until a glossy sauce forms, remove from heat, and scatter with fresh parsley.",
        ],
    ),
    Recipe(
        id=6,
        title="Berry Power Smoothie Bowl",
        description="Thick, antioxidant-packed smoothie bowl topped with sliced banana, chia seeds, and crunchy granola.",
        image=None,
        ingredients=[
            "1.5 cups frozen mixed berries (strawberries, blueberries, raspberries)",
            "1 frozen ripe banana",
            "1/2 cup Greek yogurt or almond milk",
            "1 tbsp honey or pure maple syrup",
            "Toppings: fresh berries, sliced banana, chia seeds, crunchy granola",
        ],
        steps=[
            "Add frozen berries, frozen banana, yogurt, and honey into a high-speed blender.",
            "Blend on low to high, using a tamper if needed, until thick and spoonable.",
            "Pour into a wide bowl and smooth the surface.",
            "Arrange fresh berries, banana slices, chia seeds, and granola neatly on top and serve immediately.",
        ],
    ),
]


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
