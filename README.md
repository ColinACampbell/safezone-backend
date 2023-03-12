# Safezone-backend

How to run with docker 
- Run `uvicorn app.main:app --reload --host 0.0.0.0 --port 8080` without docker
- Run `docker compose -f docker-compose.dev.yaml up --build` with docker
## Database Migrations 
Whenver you update an sqlalchemy model you will need to create a migration for it so other developers can use it

1. In the cmd/shell type `docker ps` to show all running containers 
2. COPY the id of the container running the api/backend under the column `CONTAINER_ID`
3. Enter into the container shell using the command `docker exec -it <CONTAINER_ID> bash`
4. To create a migration run `alembic revision --autogenerate -m <MESSAGE>`
5. Now just update these migration changes to the database using `alembic upgrade head`
6. To downgrade use `alembic downgrade -1`