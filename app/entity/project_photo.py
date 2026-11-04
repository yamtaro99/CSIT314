import os
import uuid

from flask import current_app

from app.db import get_db, now


class ProjectPhoto:
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
    MAX_BYTES = 10 * 1024 * 1024
    SIGNATURES = (b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n")

    def __init__(self, file=None, project_id=None, file_url=None, caption="",
                 photo_id=None, uploaded_at=None):
        self.photo_id = photo_id
        self.project_id = project_id
        self.file = file
        self.file_url = file_url
        self.caption = caption
        self.uploaded_at = uploaded_at
        self.error = None

    @property
    def filename(self):
        return (self.file.filename or "") if self.file else ""

    def _extension(self):
        name = self.filename
        return name.rsplit(".", 1)[-1].lower() if "." in name else ""

    def validate_file(self):
        if self.file is None or not self.filename:
            self.error = "No file selected"
            return False
        if self._extension() not in self.ALLOWED_EXTENSIONS:
            self.error = f"{self.filename}: only JPG and PNG files are allowed"
            return False
        stream = self.file.stream
        stream.seek(0, os.SEEK_END)
        size = stream.tell()
        stream.seek(0)
        if size == 0:
            self.error = f"{self.filename}: file is empty"
            return False
        if size > self.MAX_BYTES:
            self.error = f"{self.filename}: file is larger than 10MB"
            return False
        header = stream.read(8)
        stream.seek(0)
        if not any(header.startswith(sig) for sig in self.SIGNATURES):
            self.error = f"{self.filename}: file is not a valid image"
            return False
        return True

    def save(self):
        if self.project_id is None or not self.validate_file():
            return False
        stored_name = f"{uuid.uuid4().hex}.{self._extension()}"
        self.file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], stored_name))
        self.file_url = f"/uploads/{stored_name}"
        self.uploaded_at = now()
        conn = get_db()
        cur = conn.execute(
            "INSERT INTO project_photo (project_id, file_url, caption, uploaded_at) VALUES (?, ?, ?, ?)",
            (self.project_id, self.file_url, self.caption, self.uploaded_at),
        )
        conn.commit()
        self.photo_id = cur.lastrowid
        return True

    @classmethod
    def find_by_project(cls, project_id):
        rows = get_db().execute(
            "SELECT * FROM project_photo WHERE project_id = ? ORDER BY photo_id", (project_id,)
        ).fetchall()
        return [cls(photo_id=r["photo_id"], project_id=r["project_id"], file_url=r["file_url"],
                    caption=r["caption"], uploaded_at=r["uploaded_at"]) for r in rows]
