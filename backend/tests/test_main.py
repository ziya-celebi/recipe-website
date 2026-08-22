import pytest
from fastapi.testclient import TestClient

import store
from main import app

client = TestClient(app)

PANCAKES = {
    "title": "Pancakes",
    "description": "Fluffy breakfast pancakes with a golden crust.",
    "image": None,
    "ingredients": ["1 cup flour", "1 cup milk", "1 egg"],
    "steps": ["Whisk the dry ingredients.", "Cook until golden."],
}

SHRIMP = {
    "title": "Garlic Butter Sautéed Shrimp",
    "description": "Juicy shrimp in a rich garlic butter sauce.",
    "image": None,
    "ingredients": ["400g large shrimp", "4 cloves garlic", "3 tbsp butter"],
    "steps": ["Sear the shrimp.", "Toss with garlic butter."],
}


@pytest.fixture(autouse=True)
def reset_store(monkeypatch, tmp_path):
    monkeypatch.setenv("RECIPE_DATA_DIR", str(tmp_path))
    store.reset()
    yield
    store.reset()


@pytest.fixture
def recipes():
    return [client.post("/api/recipes", json=payload).json() for payload in (PANCAKES, SHRIMP)]


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello from FastAPI!"}


def test_list_recipes_is_empty_without_seed_data():
    response = client.get("/api/recipes")
    assert response.status_code == 200
    assert response.json() == []


def test_list_recipes(recipes):
    response = client.get("/api/recipes")
    assert response.status_code == 200
    listed = response.json()
    assert len(listed) == len(recipes)
    assert {"id", "title", "description", "image", "ingredients", "steps"} <= listed[0].keys()


def test_list_recipes_search_by_title(recipes):
    response = client.get("/api/recipes?q=pancake")
    assert response.status_code == 200
    assert [recipe["title"] for recipe in response.json()] == ["Pancakes"]


def test_list_recipes_search_by_ingredient(recipes):
    response = client.get("/api/recipes?q=shrimp")
    assert response.status_code == 200
    assert [recipe["title"] for recipe in response.json()] == ["Garlic Butter Sautéed Shrimp"]


def test_list_recipes_search_case_insensitive(recipes):
    response = client.get("/api/recipes?q=PANCAKES")
    assert response.status_code == 200
    assert [recipe["title"] for recipe in response.json()] == ["Pancakes"]


def test_list_recipes_search_no_match(recipes):
    response = client.get("/api/recipes?q=nonexistent_recipe_query")
    assert response.status_code == 200
    assert response.json() == []


def test_get_recipe(recipes):
    response = client.get(f"/api/recipes/{recipes[0]['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Pancakes"
    assert data["image"] is None


def test_get_recipe_not_found():
    response = client.get("/api/recipes/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Recipe not found"


def test_create_recipe_api():
    payload = {
        "title": "French Toast",
        "description": "Golden brioche soaked in vanilla egg custard.",
        "image": None,
        "ingredients": ["4 thick slices brioche", "2 eggs", "1/2 cup milk", "1 tsp cinnamon"],
        "steps": ["Whisk custard mixture.", "Dip bread slices.", "Cook on buttered skillet."],
    }
    response = client.post("/api/recipes", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "French Toast"
    assert data["id"] == 1


def test_delete_recipe_api(recipes):
    recipe_id = recipes[0]["id"]
    response = client.delete(f"/api/recipes/{recipe_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Recipe deleted successfully"

    # Confirm it is no longer found
    get_res = client.get(f"/api/recipes/{recipe_id}")
    assert get_res.status_code == 404


def test_admin_home_auth_required():
    response = client.get("/api/admin")
    assert response.status_code == 401


def test_admin_home_authenticated(recipes):
    response = client.get("/api/admin", auth=("admin", "admin"))
    assert response.status_code == 200
    assert "Recipe Website Admin" in response.text
    assert "Pancakes" in response.text


def test_admin_create_recipe_form():
    form_data = {
        "title": "Admin Waffles",
        "description": "Crispy Belgian waffles with strawberries.",
        "ingredients": "2 cups flour\n2 eggs\n1/2 cup butter",
        "steps": "Mix batter\nPour into waffle iron\nBake until golden",
        "image_url": "/recipes/waffles.jpg",
    }
    response = client.post(
        "/api/admin/recipes",
        data=form_data,
        auth=("admin", "admin"),
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "created=1" in response.headers["location"]


def test_admin_delete_recipe(recipes):
    response = client.post(
        f"/api/admin/recipes/{recipes[1]['id']}/delete",
        auth=("admin", "admin"),
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "deleted=1" in response.headers["location"]


def test_db_url_postgres_formatting(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@ep-cool-db.us-east-2.aws.neon.tech/neondb?sslmode=require")
    assert store.get_db_url().startswith("postgresql://")
    assert store.is_postgres() is True
    assert store.get_db_type() == "PostgreSQL (Cloud)"


def test_legacy_recipes_json_migration(monkeypatch, tmp_path):
    # Create legacy recipes.json before store initialization
    data_dir = tmp_path / "legacy_data"
    data_dir.mkdir()
    legacy_json = data_dir / "recipes.json"
    legacy_json.write_text(
        '[{"id": 1, "title": "Legacy Pasta", "description": "Classic pasta", "image": null, "ingredients": ["Pasta"], "steps": ["Boil"]}]',
        encoding="utf-8",
    )
    monkeypatch.setenv("RECIPE_DATA_DIR", str(data_dir))
    store.reset()

    # Querying recipes should automatically migrate the JSON content into SQLite
    items = store.list_recipes()
    assert len(items) == 1
    assert items[0].title == "Legacy Pasta"
    assert items[0].ingredients == ["Pasta"]

