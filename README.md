# safezone-backend

How to run with docker 
- Run `uvicorn app.main:app --reload --host 0.0.0.0 --port 8080` without docker
- Run `docker compose -f docker-compose.dev.yaml up --build` with docker