from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.database import init_db, get_connection

class TaskCreate(BaseModel):
    title: str

class TaskUpdate(BaseModel):
    title: str
    done: bool

tasks = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Walk the dog", "done": False},
    {"id": 3, "title": "Write code", "done": True},
]

app = FastAPI()

init_db()

@app.exception_handler(RequestValidationError)
def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"error": exc.errors()[0]["msg"]},
    )


@app.get("/")
def read_root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return dict(row)


@app.get("/tasks", summary="List all tasks")
def get_tasks():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM tasks").fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.post("/tasks", status_code=201, summary="create a new task")
def create_task(new_task: TaskCreate):
    next_id = max(task["id"] for task in tasks) + 1
    task = {"id": next_id, "title": new_task.title, "done": False}
    tasks.append(task)
    return task


@app.put("/tasks/{task_id}", summary="Update a task")
def update_task(task_id: int, new_update: TaskUpdate):
    for task in tasks:
        if task["id"] == task_id:
            task["title"] = new_update.title
            task["done"] = new_update.done
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task")
def delete_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            tasks.remove(task)
            return {"message": "task deleted successfully"}
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")