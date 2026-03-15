from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from database import engine
from sqlalchemy import text
from fastapi.staticfiles import StaticFiles
from fastapi import UploadFile, File
import shutil
import os
from fastapi import Request
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import RedirectResponse

app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name ="static")
# HOME PAGE
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index1.html", {"request": request})


@app.get("/developer", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("developer.html", {"request": request})

#About Us
@app.get("/aboutus", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("aboutus.html", {"request": request})

#committee Us
@app.get("/committee", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("committee.html", {"request": request})

#FAQ
@app.get("/faq")
def faq(request: Request):
    return templates.TemplateResponse(
        "faq.html",
        {"request": request}
    )


#Registration
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
    health_problem: str = Form(None)):

    if len(mobile.strip()) != 10:
        return {"error":"Mobile number must be 10 digits"}

    with engine.connect() as conn:

        conn.execute(
            text("""INSERT INTO users(name,age,mobile,address,district,state,health_problem)
            VALUES (:n,:a,:m,:ad,:d,:s,:h)"""),
            {
                "n": name,
                "a": age,
                "m": mobile,
                "ad":address ,
                "d": district,
                "s": state,
                "h": health_problem,}
                
        )

        conn.commit()

    return {"Message":"Registration Successful"}

#gallery automatically uploads folder से photos दिखाएगी।

@app.get("/gallery", response_class=HTMLResponse)
def gallery(request: Request):

    images = os.listdir("static/uploads")

    return templates.TemplateResponse(
        "gallery.html",
        {"request": request, "images": images}
    )



# SHOW BRANCHES
@app.get("/branches", response_class=HTMLResponse)
def branches(request: Request):

    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM branches"))
        data = result.fetchall()

    return templates.TemplateResponse(
        "branches.html",
        {"request": request, "branches": data}
    )

#reviews
@app.get("/reviews", response_class=HTMLResponse)
def reviews_page(request: Request):

    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM reviews ORDER BY id DESC"))
        reviews = result.fetchall()

    return templates.TemplateResponse(
        "reviews.html",
        {"request": request, "reviews": reviews}
    )

#submit review
@app.post("/submit_review")
async def submit_review(
    name: str = Form(...),
    city: str = Form(...),
    rating: int = Form(...),
    health_improvement: str = Form(...),
    message: str = Form(...),
    photo: UploadFile = File(None)
):

    photo_name = None

    if photo:
        photo_name = photo.filename
        path = f"static/reviews/{photo_name}"

        with open(path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)

    with engine.connect() as conn:

        conn.execute(
            text("""
            INSERT INTO reviews
            (name,city,rating,health_improvement,message,photo)
            VALUES(:n,:c,:r,:h,:m,:p)
            """),
            {
                "n": name,
                "c": city,
                "r": rating,
                "h": health_improvement,
                "m": message,
                "p": photo_name
            }
        )

        conn.commit()

    return {"message": "Review Submitted Successfully"}

#admin update review
@app.post("/admin/update_review/{id}")
def update_review(
    id: int,
    name: str = Form(...),
    city: str = Form(...),
    rating: int = Form(...),
    health_improvement: str = Form(...),
    message: str = Form(...),
    photo: UploadFile = File(None)
):

    filename = None

    if photo and photo.filename:
        filename = photo.filename
        filepath = f"static/uploads/{filename}"

        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)

    with engine.connect() as conn:

        if filename:
            conn.execute(
                text("""
                UPDATE reviews
                SET name=:name,
                    city=:city,
                    rating=:rating,
                    health_improvement=:health_improvement,
                    message=:message,
                    photo=:photo
                WHERE id=:id
                """),
                {
                    "name": name,
                    "city": city,
                    "rating": rating,
                    "health_improvement": health_improvement,
                    "message": message,
                    "photo": filename,
                    "id": id
                }
            )
        else:
            conn.execute(
                text("""
                UPDATE reviews
                SET name=:name,
                    city=:city,
                    rating=:rating,
                    health_improvement=:health_improvement,
                    message=:message
                WHERE id=:id
                """),
                {
                    "name": name,
                    "city": city,
                    "rating": rating,
                    "health_improvement": health_improvement,
                    "message": message,
                    "id": id
                }
            )

        conn.commit()

    return RedirectResponse("/admin/reviews", status_code=303)

#admin delete review
@app.post("/admin/delete_review/{id}")
def delete_review(id: int):

    with engine.connect() as conn:
        conn.execute(
            text("DELETE FROM reviews WHERE id=:id"),
            {"id": id}
        )
        conn.commit()

    return RedirectResponse("/admin/reviews", status_code=303)

#admin upload page
@app.get("/admin/upload", response_class=HTMLResponse)
def upload_page(request: Request):
    return templates.TemplateResponse("admin_upload.html", {"request": request})

#upload photo api
@app.post("/admin/upload_photo")
def upload_photo(photo: UploadFile = File(...)):

    filename = photo.filename
    filepath = f"static/uploads/{filename}"

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(photo.file, buffer)

    with engine.connect() as conn:
        conn.execute(
            text("INSERT INTO gallery (image) VALUES (:image)"),
            {"image": filename}
        )
        conn.commit()

    return RedirectResponse("/admin/gallery", status_code=303)



# ADD BRANCH
from fastapi import Form
from sqlalchemy import text

@app.post("/add_branch")
def add_branch(
    name: str = Form(...),
    address: str = Form(...),
    batch_time: str = Form(...),
    trainer: str = Form(...),
    contact: str = Form(...),
    map_link: str = Form(...)
):

    with engine.connect() as conn:

        conn.execute(
            text("""
            INSERT INTO branches
            (name, address, batch_time, trainer, contact, map_link)
            VALUES
            (:n, :a, :b, :t, :c, :m)
            """),
            {
                "n": name,
                "a": address,
                "b": batch_time,
                "t": trainer,
                "c": contact,
                "m": map_link
            }
        )

        conn.commit()

    return {"message": "Branch Added Successfully"}

#Edit Branch
@app.post("/edit_branch/{branch_id}")
def edit_branch(
    branch_id: int,
    name: str = Form(...),
    address: str = Form(...),
    batch_time: str = Form(...),
    trainer: str = Form(...),
    contact: str = Form(...),
    map_link: str = Form(...)
):

    with engine.connect() as conn:

        conn.execute(
            text("""
            UPDATE branches
            SET name=:n,
                address=:a,
                batch_time=:b,
                trainer=:t,
                contact=:c,
                map_link=:m
            WHERE id=:id
            """),
            {
                "n": name,
                "a": address,
                "b": batch_time,
                "t": trainer,
                "c": contact,
                "m": map_link,
                "id": branch_id
            }
        )

        conn.commit()

    return {"message": "Branch Updated Successfully"}


#Delete Branch
@app.get("/delete_branch/{branch_id}")
def delete_branch(branch_id: int):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM branches WHERE id=%s", (branch_id,))
    conn.commit()

    cur.close()
    conn.close()

    return RedirectResponse("/admin/branches", status_code=303)



#show branches
@app.get("/admin/branches", response_class=HTMLResponse)
def admin_branches(request: Request):

    with engine.connect() as conn:

        branches = conn.execute(
            text("SELECT * FROM branches order by id desc")
        ).fetchall()

    return templates.TemplateResponse(
        "admin_branches.html",
        {
            "request": request,
            "branches": branches
        }
    )

#dashboard
@app.get("/admin_dashboard", response_class=HTMLResponse)
def dashboard(request: Request):

    with engine.connect() as conn:

        users = conn.execute(
            text("SELECT COUNT(*) FROM users")
        ).scalar()

        reviews = conn.execute(
            text("SELECT COUNT(*) FROM reviews")
        ).scalar()

        branches = conn.execute(
            text("SELECT COUNT(*) FROM branches")
        ).scalar()

    # gallery photos count (from folder)
    photos = len(os.listdir("static/uploads"))

    today = datetime.now().strftime("%d %B %Y | %I:%M %p")

    return templates.TemplateResponse(
        "admin_dashboard.html",
        {
            "request": request,
            "users": users,
            "reviews": reviews,
            "branches": branches,
            "photos": photos,
            "today": today
        }
    )

#admin registration check 
@app.get("/admin/users")
def admin_users(request: Request):

    with engine.connect() as conn:

        users = conn.execute(
            text("SELECT * FROM users ORDER BY id DESC")
        ).fetchall()

    return templates.TemplateResponse(
        "admin_registration.html",
        {
            "request": request,
            "users": users
        }
    )

#delete registration
@app.post("/admin/delete_user/{id}")
def delete_user(id:int):

    with engine.connect() as conn:

        conn.execute(
            text("DELETE FROM registrations WHERE id=:id"),
            {"id": id}
        )
        conn.commit()

    return RedirectResponse("/admin/users", status_code=303)


#Admin Reviews
@app.get("/admin/reviews")
def admin_reviews(request: Request):

    with engine.connect() as conn:

        reviews = conn.execute(
            text("SELECT * FROM reviews ORDER BY id DESC")
        ).fetchall()

    return templates.TemplateResponse(
        "admin_reviews.html",
        {
            "request": request,
            "reviews": reviews
        }
    )


@app.get("/admin/gallery")
def admin_gallery(request: Request):

    with engine.connect() as conn:

        photos = conn.execute(
            text("SELECT * FROM gallery ORDER BY id DESC")
        ).fetchall()

    return templates.TemplateResponse(
        "admin_gallery.html",
        {
            "request": request,
            "photos": photos
        }
    )

    
@app.post("/admin/upload_photo")
async def upload_photo(photo: UploadFile = File(...)):

    file_location = f"static/images/{photo.filename}"

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(photo.file, buffer)

    with engine.connect() as conn:
        conn.execute(
            text("INSERT INTO gallery(image) VALUES(:image)"),
            {"image": photo.filename}
        )
        conn.commit()

    return RedirectResponse("/admin/gallery", status_code=303)





@app.post("/admin/delete_photo/{id}")
def delete_photo(id:int):

    with engine.connect() as conn:

        photo = conn.execute(
            text("SELECT image FROM gallery WHERE id=:id"),
            {"id": id}
        ).fetchone()

        if photo:

            file_path = f"static/images/{photo.image}"

            if os.path.exists(file_path):
                os.remove(file_path)

            conn.execute(
                text("DELETE FROM gallery WHERE id=:id"),
                {"id": id}
            )
            conn.commit()

    return RedirectResponse("/admin/gallery", status_code=303)
