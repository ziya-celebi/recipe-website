for deployment

sudo docker build -t fastapi-backend .
sudo docker run -d -p 8000:8000 --name fastapi-backend fastapi-backend
curl http://localhost:8000/

for dev

for .venv: uv sync
uv run uvicorn main:app --reload
