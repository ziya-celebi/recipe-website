from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from auth import require_admin
from models import RecipeCreate
from store import create_recipe, delete_recipe, list_recipes, uploads_dir

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}

router = APIRouter(prefix="/api/admin", dependencies=[Depends(require_admin)])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))


def _lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def _save_image(image: UploadFile | None, image_url: str = "") -> str | None:
    if image is not None and image.filename:
        suffix = ALLOWED_IMAGE_TYPES.get(image.content_type or "")
        if suffix is None:
            suffix = Path(image.filename).suffix.lower()
            if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
                suffix = None
            elif suffix == ".jpeg":
                suffix = ".jpg"
        if suffix:
            filename = f"{uuid4().hex}{suffix}"
            dest = uploads_dir() / filename
            dest.write_bytes(image.file.read())
            return f"/media/{filename}"
    clean_url = image_url.strip()
    return clean_url if clean_url else None


@router.get("", response_class=HTMLResponse)
def admin_home(
    request: Request,
    created: int | None = None,
    deleted: int | None = None,
    error: str | None = None,
):
    return templates.TemplateResponse(
        request,
        "admin.html",
        {
            "recipes": list_recipes(),
            "created": created == 1,
            "deleted": deleted == 1,
            "error": error,
        },
    )


@router.post("/recipes")
async def admin_create_recipe(
    request: Request,
    title: str = Form(),
    description: str = Form(""),
    ingredients: str = Form(""),
    steps: str = Form(""),
    image_url: str = Form(""),
    image: UploadFile | None = File(None),
):
    title = title.strip()
    if not title:
        return templates.TemplateResponse(
            request,
            "admin.html",
            {
                "recipes": list_recipes(),
                "created": False,
                "deleted": False,
                "error": "Recipe title is required.",
            },
            status_code=400,
        )

    recipe = create_recipe(
        RecipeCreate(
            title=title,
            description=description.strip(),
            image=_save_image(image, image_url),
            ingredients=_lines(ingredients),
            steps=_lines(steps),
        )
    )
    return RedirectResponse(url=f"/api/admin?created=1&id={recipe.id}", status_code=303)


@router.post("/recipes/{recipe_id}/delete")
def admin_delete_recipe(recipe_id: int):
    delete_recipe(recipe_id)
    return RedirectResponse(url="/admin?deleted=1", status_code=303)
