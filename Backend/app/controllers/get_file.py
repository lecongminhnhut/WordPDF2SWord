from flask_restful import Resource
from flask import send_from_directory, jsonify
from werkzeug.utils import secure_filename
import os
from app.main.settings import Config

# Path to the folder where files are stored
DATASET_FOLDER = os.path.abspath(os.path.join(Config.CHROMA_DB_PATH, 'files_upload'))
GET_FILE_ROUTE = '/get-file/<path:filename>'

class GetFile(Resource):
    def __init__(self):
        self.dataset_folder = DATASET_FOLDER

    def get(self, filename):
        try:
            # Sanitize and secure the filename
            safe_filename = secure_filename(filename)

            # Ensure the file exists
            file_path = os.path.join(self.dataset_folder, safe_filename)

            print(f"File path: {file_path}")
            
            if not os.path.exists(file_path):
                return jsonify({'message': 'File not found'}), 404

            # Send the file as an attachment with the cleaned filename
            return send_from_directory(
                directory=self.dataset_folder,
                path=safe_filename,
                as_attachment=True
            )
        except Exception as e:
            # Return an error response if something goes wrong
            return jsonify({'message': f'Error retrieving file: {str(e)}'}), 500