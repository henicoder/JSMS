import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "development-only-secret")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///jewellery_shop_dev.db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAX_CONTENT_LENGTH = 4 * 1024 * 1024

    UPLOAD_FOLDER = os.path.join(
        os.getcwd(),
        "app",
        "static",
        "uploads",
        "products"
    )