import os
import uuid
from pathlib import Path

from werkzeug.utils import secure_filename
from flask import current_app


ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "txt"}


def validate_file(file):
    if not file or not file.filename:
        return False

    safe_name = secure_filename(file.filename)

    if not safe_name or "." not in safe_name:
        return False

    extension = safe_name.rsplit(".", 1)[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        return False

    content = file.stream.read(16)
    file.stream.seek(0)

    # Check file signatures
    if extension == "pdf":
        return content.startswith(b"%PDF-")

    if extension == "png":
        return content.startswith(b"\x89PNG\r\n\x1a\n")

    if extension in {"jpg", "jpeg"}:
        return content.startswith(b"\xff\xd8\xff")

    if extension == "txt":
        try:
            file.stream.read().decode("utf-8")
            file.stream.seek(0)
            return True
        except UnicodeDecodeError:
            file.stream.seek(0)
            return False

    return False


def save_document(file):
    if not validate_file(file):
        raise ValueError("Unsupported or invalid file.")

    original_name = secure_filename(file.filename)

    extension = original_name.rsplit(".", 1)[1].lower()

    # Generate an unpredictable internal filename
    stored_name = f"{uuid.uuid4().hex}.{extension}"

    # Store outside the public static folder
    project_root = Path(current_app.root_path).parent
    storage_folder = project_root / "private_storage"

    storage_folder.mkdir(parents=True, exist_ok=True)

    file_path = storage_folder / stored_name

    # Exclusive creation prevents accidental overwriting
    with open(file_path, "xb") as destination:
        file.save(destination)

    return original_name, stored_name



def delete_document(stored_name):
    if not stored_name:
        return False

    try:
        name, extension = stored_name.rsplit(".", 1)

        if extension not in ALLOWED_EXTENSIONS:
            return False

        if len(name) != 32:
            return False

        if uuid.UUID(hex=name).hex != name:
            return False

    except (ValueError, AttributeError):
        return False

    project_root = Path(current_app.root_path).parent
    storage_folder = project_root / "private_storage"
    file_path = storage_folder / stored_name

    # Ensure the resolved file remains inside private storage
    if file_path.resolve().parent != storage_folder.resolve():
        return False

    if file_path.is_file():
        os.remove(file_path)
        return True

    return False
