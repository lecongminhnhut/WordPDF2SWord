import os
from werkzeug.utils import secure_filename

class FileService:
    ALLOWED_EXTENSIONS = {'pdf', 'docx'}

    def __init__(self, upload_folder):
        self.upload_folder = upload_folder
        os.makedirs(self.upload_folder, exist_ok=True)  # Ensure the upload folder exists

    def is_valid_file(self, filename):
        """
        Check if the uploaded file has a valid extension.
        """
        if '.' in filename:
            ext = filename.rsplit('.', 1)[1].lower()
            return ext in self.ALLOWED_EXTENSIONS
        return False

    def save_file(self, file, user_id):
        """
        Save the file with a user-specific prefix to avoid conflicts.
        """
        filename = secure_filename(file.filename)
        filename = f'{user_id}_{filename}'
        filepath = os.path.join(self.upload_folder, filename)
        file.save(filepath)
        return filepath
    
    def file_exists(self, filename):
        # Ensure the filename is secure and exists in the dataset folder
        safe_filename = secure_filename(filename)
        file_path = os.path.join(self.dataset_folder, safe_filename)
        return os.path.exists(file_path)