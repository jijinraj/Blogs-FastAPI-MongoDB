from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from mongodb_config import (
    MONGO_DB_HOST,
    MONGO_DB_PORT,
    MONGO_DB_NAME,
    MONGO_DB_USERNAME,
    MONGO_DB_PASSWORD,
)


from cryptography.fernet import Fernet

app = FastAPI()

# Replace this key with your own generated key (keep it safe!)
ENCRYPTION_KEY = b'mjKHkrUGVP-zoJQGLVydZ_NuoD3A4k1SEIDgFj6bSsI='

# MongoDB setup with authentication
client = MongoClient(
    f"mongodb://{MONGO_DB_USERNAME}:{MONGO_DB_PASSWORD}@{MONGO_DB_HOST}:{MONGO_DB_PORT}/"
)
db = client[MONGO_DB_NAME]
collection = db["blogs"]

# Data model for blog posts
class BlogPost(BaseModel):
    title: str
    content: str

# Encrypt data before saving it to MongoDB
def encrypt_data(key, data):
    f = Fernet(key)
    return f.encrypt(data.encode()).decode()

# Decrypt data after retrieving it from MongoDB
def decrypt_data(key, encrypted_data):
    f = Fernet(key)
    return f.decrypt(encrypted_data.encode()).decode()

# Encrypt data before saving it to MongoDB
def encrypt_and_save_blog(blog: BlogPost):
    encrypted_data = {
        "title": encrypt_data(ENCRYPTION_KEY, blog.title),
        "content": encrypt_data(ENCRYPTION_KEY, blog.content),
    }
    collection.insert_one(encrypted_data)

# Decrypt data after retrieving it from MongoDB
def decrypt_blog_data(blog_data):
    return {
        # "title": decrypt_data(ENCRYPTION_KEY, blog_data["title"]),
        # "content": decrypt_data(ENCRYPTION_KEY, blog_data["content"]),
            "title": blog_data["title"],
            "content": blog_data["content"],

    }

@app.post("/blogs/", status_code=201)
def create_blog(blog: BlogPost):
    encrypt_and_save_blog(blog)
    return {"message": "Blog post created successfully"}

@app.get("/blogs/{blog_id}", response_model=BlogPost)
def get_blog(blog_id: str):
    blog_data = collection.find_one({"_id": blog_id})
    if blog_data:
        return decrypt_blog_data(blog_data)
    raise HTTPException(status_code=404, detail="Blog not found")

@app.put("/blogs/{blog_id}", response_model=BlogPost)
def update_blog(blog_id: str, blog: BlogPost):
    existing_blog_data = collection.find_one({"_id": blog_id})
    if existing_blog_data:
        encrypted_data = {
            "$set": {
                "title": encrypt_data(ENCRYPTION_KEY, blog.title),
                "content": encrypt_data(ENCRYPTION_KEY, blog.content),
            }
        }
        collection.update_one({"_id": blog_id}, encrypted_data)
        return {"message": "Blog post updated successfully"}
    raise HTTPException(status_code=404, detail="Blog not found")

@app.delete("/blogs/{blog_id}", status_code=204)
def delete_blog(blog_id: str):
    result = collection.delete_one({"_id": blog_id})
    if result.deleted_count == 1:
        return {"message": "Blog post deleted successfully"}
    raise HTTPException(status_code=404, detail="Blog not found")

@app.get("/blogs/", response_model=list[BlogPost])
def get_all_blogs():
    blogs = list(collection.find())
    for blog in blogs:
        # print(blogs)
        print("pritning blog")
        print(blog)
        print("printing value blog in the single blog ! ")
        print(blog["title"])
        # return [decrypt_data(ENCRYPTION_KEY, blog)]
        return blogs