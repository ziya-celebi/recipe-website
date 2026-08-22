import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request as UrlRequest, urlopen
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from auth import require_admin
from models import RecipeCreate
from store import create_recipe, delete_recipe, get_db_type, list_recipes, save_image

try:
    import cloudinary
    import cloudinary.uploader

    _CLOUDINARY_AVAILABLE = True
except ImportError:
    _CLOUDINARY_AVAILABLE = False

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


class ImageUploadError(RuntimeError):
    pass


router = APIRouter(prefix="/api/admin", dependencies=[Depends(require_admin)])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))


def _site_base() -> str:
    return os.environ.get("SITE_BASE_URL", "").rstrip("/")


def _lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def _image_suffix(image: UploadFile) -> str | None:
    suffix = ALLOWED_IMAGE_TYPES.get(image.content_type or "")
    if suffix is not None:
        return suffix

    suffix = Path(image.filename or "").suffix.lower()
    if suffix == ".jpeg":
        return ".jpg"
    if suffix in {".jpg", ".png", ".webp", ".gif"}:
        return suffix
    return None


def _upload_to_supabase(image: UploadFile, suffix: str) -> str | None:
    secret_key = os.environ.get("SUPABASE_SECRET_KEY", "").strip()
    service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    storage_key = secret_key or service_role_key
    if not storage_key:
        return None

    supabase_url = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
    if not supabase_url:
        raise ImageUploadError("SUPABASE_URL is required for Supabase Storage uploads.")

    bucket = os.environ.get("SUPABASE_STORAGE_BUCKET", "recipe-images").strip()
    if not bucket:
        raise ImageUploadError("SUPABASE_STORAGE_BUCKET cannot be empty.")

    object_path = f"recipes/{uuid4().hex}{suffix}"
    encoded_bucket = quote(bucket, safe="")
    encoded_path = quote(object_path, safe="/")
    upload_url = f"{supabase_url}/storage/v1/object/{encoded_bucket}/{encoded_path}"
    headers = {
        "apikey": storage_key,
        "Content-Type": image.content_type or "application/octet-stream",
        "x-upsert": "false",
    }
    if not secret_key:
        headers["Authorization"] = f"Bearer {service_role_key}"

    request = UrlRequest(
        upload_url,
        data=image.file.read(),
        method="POST",
        headers=headers,
    )

    try:
        with urlopen(request, timeout=20):
            pass
    except HTTPError as exc:
        raise ImageUploadError(
            f"Supabase Storage upload failed with status {exc.code}. "
            "Check the bucket name and secret key."
        ) from exc
    except URLError as exc:
        raise ImageUploadError("Supabase Storage could not be reached.") from exc

    return (
        f"{supabase_url}/storage/v1/object/public/"
        f"{encoded_bucket}/{encoded_path}"
    )


def _save_image(image: UploadFile | None, image_url: str = "") -> str | None:
    if image is not None and image.filename:
        suffix = _image_suffix(image)
        if suffix is None:
            raise ImageUploadError("Upload a JPG, PNG, WebP, or GIF image.")

        supabase_url = _upload_to_supabase(image, suffix)
        if supabase_url:
            return supabase_url

        if _CLOUDINARY_AVAILABLE and os.environ.get("CLOUDINARY_URL"):
            try:
                res = cloudinary.uploader.upload(
                    image.file,
                    folder="recipe_website",
                    resource_type="image",
                )
                return res.get("secure_url") or res.get("url")
            except Exception as e:
                print(f"Cloudinary upload failed: {e}")

        filename = f"{uuid4().hex}{suffix}"
        save_image(
            filename,
            image.content_type or "application/octet-stream",
            image.file.read(),
        )
        return f"/api/media/{filename}"
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
            "site_base": _site_base(),
            "db_type": get_db_type(),
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
                "site_base": _site_base(),
            },
            status_code=400,
        )

    try:
        saved_image = _save_image(image, image_url)
    except ImageUploadError as exc:
        return templates.TemplateResponse(
            request,
            "admin.html",
            {
                "recipes": list_recipes(),
                "created": False,
                "deleted": False,
                "error": str(exc),
                "site_base": _site_base(),
                "db_type": get_db_type(),
            },
            status_code=502,
        )

    recipe = create_recipe(
        RecipeCreate(
            title=title,
            description=description.strip(),
            image=saved_image,
            ingredients=_lines(ingredients),
            steps=_lines(steps),
        )
    )
    return RedirectResponse(url=f"/api/admin?created=1&id={recipe.id}", status_code=303)


@router.post("/recipes/{recipe_id}/delete")
def admin_delete_recipe(recipe_id: int):
    delete_recipe(recipe_id)
    return RedirectResponse(url="/api/admin?deleted=1", status_code=303)
