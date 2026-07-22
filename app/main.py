from fastapi import FastAPI, HTTPException, Request, Depends
from pydantic import BaseModel
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.database import init_db, get_connection
from app.auth import supabase
from app.auth import get_current_user

class TaskCreate(BaseModel):
    title: str

class TaskUpdate(BaseModel):
    title: str
    done: bool

class AuthRequest(BaseModel):
    email: str
    password: str


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
    row = conn.execute("SELECT * FROM tasks WHERE id = %s", (task_id,)).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return row


@app.get("/tasks", summary="List all tasks")
def get_tasks():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM tasks").fetchall()
    conn.close()
    return [(row) for row in rows]


@app.post("/tasks", status_code=201, summary="create a new task")
def create_task(new_task: TaskCreate):
    conn = get_connection()
    row = conn.execute(
        "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING *",
        (new_task.title, False)
    ).fetchone()
    conn.commit()
    conn.close()
    return row


@app.put("/tasks/{task_id}", summary="Update a task")
def update_task(task_id: int, new_update: TaskUpdate):
    conn = get_connection()
    row = conn.execute("SELECT * FROM tasks WHERE id = %s", (task_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    row = conn.execute("UPDATE tasks SET title = %s, done = %s WHERE id = %s", (new_update.title, new_update.done, task_id))
    conn.commit()
    conn.close()

    return {"id": task_id, "title": new_update.title, "done": new_update.done}
    


@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task")
def delete_task(task_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM tasks WHERE id = %s", (task_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    row = conn.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    conn.commit()
    conn.close()


# sign up route
@app.post("/auth/signup", status_code=201)
def signup(credentials: AuthRequest):
    result = supabase.auth.sign_up({
        "email": credentials.email,
        "password": credentials.password
    })
    return {"user": result.user}


# login route
@app.post("/auth/login")
def login(credentials: AuthRequest):
    try:
        result = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid login credentials")

    return {
        "access_token": result.session.access_token,
        "refresh_token": result.session.refresh_token
    }


# publicly accessible route - no middleware
@app.get("/public/info")
def public_info():
    return {"message": "Welcome stranger! This info is public."}


# protected route - theres middleware
@app.get("/protected/profile")
def profile(current_user = Depends(get_current_user)):
    return {"id": current_user.id, "email": current_user.email, "created_at": current_user.created_at}


# Log Out route
@app.post("/auth/logout", status_code=204)
def logout(current_user = Depends(get_current_user)):
    supabase.auth.sign_out()
    return {"message": "log out successful"}


@app.get("/protected/dashboard")
def dashboard(current_user = Depends(get_current_user)):
    return {"message": f"Welcome to your dashboard, {current_user.email}"}