from fastapi import FastAPI, Form, Request, UploadFile, File, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from database import engine, SessionLocal
from models import Base, Admin
from schemas import AdminCreate
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
import shutil
import os

# 🔥 Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# 🔥 Ensure folders exist (Render fix)
os.makedirs("static/uploads", exist_ok=True)
os.makedirs("static/images", exist_ok=True)
os.makedirs("static/reviews", exist_ok=True)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# 🔐 SECURITY
SECRET_KEY = os.getenv("SECRET_KEY", "fallbackkey")
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def create_token(data: dict):
    data.update({"exp": datetime.utcnow() + timedelta(hours=2)})
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(request: Request):
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Not logged in")
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ------------------ PUBLIC PAGES ------------------

@app.get("/", response_class=HTMLResponse)
def home_page(request: Request):
    return templates.TemplateResponse("index1.html", {"request": request})

@app.get("/donate", response_class=HTMLResponse)
def donate_page(request: Request):
    return templates.TemplateResponse("donate.html", {"request": request})

@app.get("/developer", response_class=HTMLResponse)
def developer_page(request: Request):
    return templates.TemplateResponse("developer.html", {"request": request})

@app.get("/aboutus", response_class=HTMLResponse)
def about_page(request: Request):
    return templates.TemplateResponse("aboutus.html", {"request": request})

@app.get("/committee", response_class=HTMLResponse)
def committee_page(request: Request):
    return templates.TemplateResponse("committee.html", {"request": request})

@app.get("/faq", response_class=HTMLResponse)
def faq_page(request: Request):
    return templates.TemplateResponse("faq.html", {"request": request})

# ------------------ REGISTRATION ------------------

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/submit_registration")
def submit_registration(
    name: str = Form(...),
    age: int = Form(...),
    mobile: str = Form(...),
    address: str = Form(...),
    district: str = Form(...),
    state: str = Form(...),
    health_problem: str = Form(None)
):
    if len(mobile.strip()) != 10:
        return {"error": "Mobile must be 10 digits"}

    with engine.connect() as conn:
        conn.execute(
            text("""
            INSERT INTO users(name,age,mobile,address,district,state,health_problem)
            VALUES (:n,:a,:m,:ad,:d,:s,:h)
            """),
            {"n": name, "a": age, "m": mobile, "ad": address,
             "d": district, "s": state, "h": health_problem}
        )
        conn.commit()

    return {"message": "Registration Successful"}

# ------------------ GALLERY ------------------

@app.get("/gallery", response_class=HTMLResponse)
def gallery(request: Request):
    images = os.listdir("static/uploads")
    return templates.TemplateResponse("gallery.html", {"request": request, "images": images})

# ------------------ ADMIN AUTH ------------------

@app.post("/register-admin")
def register_admin(admin: AdminCreate):
    db = SessionLocal()
    try:
        if db.query(Admin).filter(Admin.email == admin.email).first():
            raise HTTPException(400, "Email exists")

        new_admin = Admin(
            name=admin.name,
            email=admin.email,
            password=hash_password(admin.password),
            role="admin",
            is_approved=False
        )
        db.add(new_admin)
        db.commit()
        return {"message": "Waiting for approval"}
    finally:
        db.close()

@app.get("/login-page", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    try:
        admin = db.query(Admin).filter(Admin.email == email).first()
        if not admin or not verify_password(password, admin.password):
            return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

        if admin.role == "admin" and not admin.is_approved:
            return templates.TemplateResponse("login.html", {"request": request, "error": "Not approved"})

        token = create_token({"admin_id": admin.id, "role": admin.role})

        res = RedirectResponse("/admin_dashboard", status_code=303)
        res.set_cookie("token", token, httponly=True)
        return res
    finally:
        db.close()

@app.get("/logout")
def logout():
    res = RedirectResponse("/login-page", status_code=303)
    res.delete_cookie("token")
    return res

# ------------------ ADMIN DASHBOARD ------------------

@app.get("/admin_dashboard", response_class=HTMLResponse)
def dashboard(request: Request, user=Depends(verify_token)):
    with engine.connect() as conn:
        users = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
        reviews = conn.execute(text("SELECT COUNT(*) FROM reviews")).scalar()
        branches = conn.execute(text("SELECT COUNT(*) FROM branches")).scalar()

    photos = len(os.listdir("static/uploads"))
    today = datetime.now().strftime("%d %B %Y")

    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "users": users,
        "reviews": reviews,
        "branches": branches,
        "photos": photos,
        "today": today
    })

# ------------------ ADMIN USERS ------------------

@app.get("/admin/users", response_class=HTMLResponse)
def admin_users(request: Request, user=Depends(verify_token)):
    with engine.connect() as conn:
        users = conn.execute(text("SELECT * FROM users")).fetchall()

    return templates.TemplateResponse("admin_registration.html", {"request": request, "users": users})

@app.post("/admin/delete_user/{id}")
def delete_user(id: int, user=Depends(verify_token)):
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM users WHERE id=:id"), {"id": id})
        conn.commit()
    return RedirectResponse("/admin/users", status_code=303)

# ------------------ RUN (Render fix) ------------------

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)



# from fastapi import FastAPI, Form, Request
# from fastapi.responses import HTMLResponse
# from fastapi.templating import Jinja2Templates
# from database import engine
# from sqlalchemy import text
# from fastapi.staticfiles import StaticFiles
# from fastapi import UploadFile, File
# import shutil
# import os
# from fastapi import Request
# from jose import JWTError, jwt
# from datetime import datetime, timedelta
# from passlib.context import CryptContext
# from fastapi import Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer
# from fastapi.responses import RedirectResponse

# import os
# print("DB URL:", os.getenv("DATABASE_URL"))

# app = FastAPI()

# templates = Jinja2Templates(directory="templates")

# app.mount("/static", StaticFiles(directory="static"), name ="static")






# # HOME PAGE
# @app.get("/", response_class=HTMLResponse)
# def home(request: Request):
#     return templates.TemplateResponse("index1.html", {"request": request})

# # donate 
# @app.get("/donate", response_class=HTMLResponse)
# def donate_us(request: Request):
#     return templates.TemplateResponse("donate.html", {"request": request})

# @app.get("/developer", response_class=HTMLResponse)
# def home(request: Request):
#     return templates.TemplateResponse("developer.html", {"request": request})

# #About Us
# @app.get("/aboutus", response_class=HTMLResponse)
# def home(request: Request):
#     return templates.TemplateResponse("aboutus.html", {"request": request})

# #committee Us
# @app.get("/committee", response_class=HTMLResponse)
# def home(request: Request):
#     return templates.TemplateResponse("committee.html", {"request": request})

# #FAQ
# @app.get("/faq")
# def faq(request: Request):
#     return templates.TemplateResponse(
#         "faq.html",
#         {"request": request}
#     )


# #Registration
# @app.get("/register", response_class=HTMLResponse)
# def register_page(request: Request):
#     return templates.TemplateResponse("register.html", {"request": request})

# @app.post("/submit_registration")
# def submit_registration(
#     name: str = Form(...),
#     age: int = Form(...),
#     mobile: str = Form(...),
#     address: str = Form(...),
#     district: str = Form(...),
#     state: str = Form(...),
#     health_problem: str = Form(None)):

#     if len(mobile.strip()) != 10:
#         return {"error":"Mobile number must be 10 digits"}

#     with engine.connect() as conn:

#         conn.execute(
#             text("""INSERT INTO registrations(name,age,mobile,address,district,state,health_problem)
#             VALUES (:n,:a,:m,:ad,:d,:s,:h)"""),
#             {
#                 "n": name,
#                 "a": age,
#                 "m": mobile,
#                 "ad":address ,
#                 "d": district,
#                 "s": state,
#                 "h": health_problem,}
                
#         )

#         conn.commit()

#     return {"Message":"Registration Successful"}

# #gallery automatically uploads folder से photos दिखाएगी।

# @app.get("/gallery", response_class=HTMLResponse)
# def gallery(request: Request):

#     images = os.listdir("static/uploads")

#     return templates.TemplateResponse(
#         "gallery.html",
#         {"request": request, "images": images}
#     )



# # SHOW BRANCHES
# @app.get("/branches", response_class=HTMLResponse)
# def branches(request: Request):

#     with engine.connect() as conn:
#         result = conn.execute(text("SELECT * FROM branches"))
#         data = result.fetchall()

#     return templates.TemplateResponse(
#         "branches.html",
#         {"request": request, "branches": data}
#     )

# #reviews
# @app.get("/reviews", response_class=HTMLResponse)
# def reviews_page(request: Request):

#     with engine.connect() as conn:
#         result = conn.execute(text("SELECT * FROM reviews ORDER BY id DESC"))
#         reviews = result.fetchall()

#     return templates.TemplateResponse(
#         "reviews.html",
#         {"request": request, "reviews": reviews}
#     )

# #submit review
# @app.post("/submit_review")
# async def submit_review(
#     name: str = Form(...),
#     city: str = Form(...),
#     rating: int = Form(...),
#     health_improvement: str = Form(...),
#     message: str = Form(...),
#     photo: UploadFile = File(None)
# ):

#     photo_name = None

#     if photo:
#         photo_name = photo.filename
#         path = f"static/reviews/{photo_name}"

#         with open(path, "wb") as buffer:
#             shutil.copyfileobj(photo.file, buffer)

#     with engine.connect() as conn:

#         conn.execute(
#             text("""
#             INSERT INTO reviews
#             (name,city,rating,health_improvement,message,photo)
#             VALUES(:n,:c,:r,:h,:m,:p)
#             """),
#             {
#                 "n": name,
#                 "c": city,
#                 "r": rating,
#                 "h": health_improvement,
#                 "m": message,
#                 "p": photo_name
#             }
#         )

#         conn.commit()

#     return {"message": "Review Submitted Successfully"}

# #admin update review
# @app.post("/admin/update_review/{id}")
# def update_review(
#     id: int,
#     name: str = Form(...),
#     city: str = Form(...),
#     rating: int = Form(...),
#     health_improvement: str = Form(...),
#     message: str = Form(...),
#     photo: UploadFile = File(None)
# ):

#     filename = None

#     if photo and photo.filename:
#         filename = photo.filename
#         filepath = f"static/uploads/{filename}"

#         with open(filepath, "wb") as buffer:
#             shutil.copyfileobj(photo.file, buffer)

#     with engine.connect() as conn:

#         if filename:
#             conn.execute(
#                 text("""
#                 UPDATE reviews
#                 SET name=:name,
#                     city=:city,
#                     rating=:rating,
#                     health_improvement=:health_improvement,
#                     message=:message,
#                     photo=:photo
#                 WHERE id=:id
#                 """),
#                 {
#                     "name": name,
#                     "city": city,
#                     "rating": rating,
#                     "health_improvement": health_improvement,
#                     "message": message,
#                     "photo": filename,
#                     "id": id
#                 }
#             )
#         else:
#             conn.execute(
#                 text("""
#                 UPDATE reviews
#                 SET name=:name,
#                     city=:city,
#                     rating=:rating,
#                     health_improvement=:health_improvement,
#                     message=:message
#                 WHERE id=:id
#                 """),
#                 {
#                     "name": name,
#                     "city": city,
#                     "rating": rating,
#                     "health_improvement": health_improvement,
#                     "message": message,
#                     "id": id
#                 }
#             )

#         conn.commit()

#     return RedirectResponse("/admin/reviews", status_code=303)

# #admin delete review
# @app.post("/admin/delete_review/{id}")
# def delete_review(id: int):

#     with engine.connect() as conn:
#         conn.execute(
#             text("DELETE FROM reviews WHERE id=:id"),
#             {"id": id}
#         )
#         conn.commit()

#     return RedirectResponse("/admin/reviews", status_code=303)

# #admin upload page
# @app.get("/admin/upload", response_class=HTMLResponse)
# def upload_page(request: Request):
#     return templates.TemplateResponse("admin_upload.html", {"request": request})

# # ADD BRANCH
# from fastapi import Form
# from sqlalchemy import text

# @app.post("/add_branch")
# def add_branch(
#     name: str = Form(...),
#     address: str = Form(...),
#     batch_time: str = Form(...),
#     trainer: str = Form(...),
#     contact: str = Form(...),
#     map_link: str = Form(...)
# ):

#     with engine.connect() as conn:

#         conn.execute(
#             text("""
#             INSERT INTO branches
#             (name, address, batch_time, trainer, contact, map_link)
#             VALUES
#             (:n, :a, :b, :t, :c, :m)
#             """),
#             {
#                 "n": name,
#                 "a": address,
#                 "b": batch_time,
#                 "t": trainer,
#                 "c": contact,
#                 "m": map_link
#             }
#         )

#         conn.commit()

#     return {"message": "Branch Added Successfully"}

# #Edit Branch
# @app.post("/edit_branch/{branch_id}")
# def edit_branch(
#     branch_id: int,
#     name: str = Form(...),
#     address: str = Form(...),
#     batch_time: str = Form(...),
#     trainer: str = Form(...),
#     contact: str = Form(...),
#     map_link: str = Form(...)
# ):

#     with engine.connect() as conn:

#         conn.execute(
#             text("""
#             UPDATE branches
#             SET name=:n,
#                 address=:a,
#                 batch_time=:b,
#                 trainer=:t,
#                 contact=:c,
#                 map_link=:m
#             WHERE id=:id
#             """),
#             {
#                 "n": name,
#                 "a": address,
#                 "b": batch_time,
#                 "t": trainer,
#                 "c": contact,
#                 "m": map_link,
#                 "id": branch_id
#             }
#         )

#         conn.commit()

#     return {"message": "Branch Updated Successfully"}


# #Delete Branch
# @app.get("/delete_branch/{branch_id}")
# def delete_branch(branch_id: int):

#     with engine.connect() as conn:
#         conn.execute(
#             text("DELETE FROM branches WHERE id=:id"),
#             {"id": branch_id}
#         )
#         conn.commit()

#     return RedirectResponse("/admin/branches", status_code=303)



# #show branches
# @app.get("/admin/branches", response_class=HTMLResponse)
# def admin_branches(request: Request):

#     with engine.connect() as conn:

#         branches = conn.execute(
#             text("SELECT * FROM branches order by id desc")
#         ).fetchall()

#     return templates.TemplateResponse(
#         "admin_branches.html",
#         {
#             "request": request,
#             "branches": branches
#         }
#     )

# #dashboard
# @app.get("/admin_dashboard", response_class=HTMLResponse)
# def dashboard(request: Request):

#     with engine.connect() as conn:

#         registrations = conn.execute(
#             text("SELECT COUNT(*) FROM registrations")
#         ).scalar()

#         reviews = conn.execute(
#             text("SELECT COUNT(*) FROM reviews")
#         ).scalar()

#         branches = conn.execute(
#             text("SELECT COUNT(*) FROM branches")
#         ).scalar()

#     # gallery photos count (from folder)
#     photos = len(os.listdir("static/uploads"))

#     today = datetime.now().strftime("%d %B %Y | %I:%M %p")

#     return templates.TemplateResponse(
#         "admin_dashboard.html",
#         {
#             "request": request,
#             "registrations": registrations,
#             "reviews": reviews,
#             "branches": branches,
#             "photos": photos,
#             "today": today
#         }
#     )

# #admin registration check 
# @app.get("/admin/registrations")
# def admin_registrations(request: Request):

#     with engine.connect() as conn:

#         registrations = conn.execute(
#             text("SELECT * FROM registrations ORDER BY id DESC")
#         ).fetchall()

#     return templates.TemplateResponse(
#         "admin_registration.html",
#         {
#             "request": request,
#             "registrations": registrations
#         }
#     )

# #delete registration
# @app.post("/admin/delete_user/{id}")
# def delete_user(id:int):

#     with engine.connect() as conn:

#         conn.execute(
#             text("DELETE FROM registrations WHERE id=:id"),
#             {"id": id}
#         )
#         conn.commit()

#     return RedirectResponse("/admin/registrations", status_code=303)


# #Admin Reviews
# @app.get("/admin/reviews")
# def admin_reviews(request: Request):

#     with engine.connect() as conn:

#         reviews = conn.execute(
#             text("SELECT * FROM reviews ORDER BY id DESC")
#         ).fetchall()

#     return templates.TemplateResponse(
#         "admin_reviews.html",
#         {
#             "request": request,
#             "reviews": reviews
#         }
#     )


# @app.get("/admin/gallery")
# def admin_gallery(request: Request):

#     with engine.connect() as conn:

#         photos = conn.execute(
#             text("SELECT * FROM gallery ORDER BY id DESC")
#         ).fetchall()

#     return templates.TemplateResponse(
#         "admin_gallery.html",
#         {
#             "request": request,
#             "photos": photos
#         }
#     )

    
# @app.post("/admin/upload_photo")
# async def upload_photo(photo: UploadFile = File(...)):

#     file_location = f"static/images/{photo.filename}"

#     with open(file_location, "wb") as buffer:
#         shutil.copyfileobj(photo.file, buffer)

#     with engine.connect() as conn:
#         conn.execute(
#             text("INSERT INTO gallery(image) VALUES(:image)"),
#             {"image": photo.filename}
#         )
#         conn.commit()

#     return RedirectResponse("/admin/gallery", status_code=303)





# @app.post("/admin/delete_photo/{id}")
# def delete_photo(id:int):

#     with engine.connect() as conn:

#         photo = conn.execute(
#             text("SELECT image FROM gallery WHERE id=:id"),
#             {"id": id}
#         ).fetchone()

#         if photo:

#             file_path = f"static/images/{photo.image}"

#             if os.path.exists(file_path):
#                 os.remove(file_path)

#             conn.execute(
#                 text("DELETE FROM gallery WHERE id=:id"),
#                 {"id": id}
#             )
#             conn.commit()

#     return RedirectResponse("/admin/gallery", status_code=303)
