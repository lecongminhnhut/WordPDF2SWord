from flask_restful import Resource, reqparse
from werkzeug.datastructures import FileStorage
from app.services.upload_file_service import FileService
import os
from app.main.settings import Config

UPLOAD_FOLDER = os.path.abspath(os.path.join(Config.CHROMA_DB_PATH, 'files_upload'))
UPLOAD_FILE_ROUTE = '/upload-file'

class UploadFile(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('file', type=FileStorage, location='files', required=True, help='File is required')
        self.parser.add_argument('user_id', type=str, location='form', required=True, help='User ID is required')  # Updated 'json' to 'form'
        self.file_service = FileService(UPLOAD_FOLDER)

    def post(self):
        args = self.parser.parse_args()
        uploaded_file = args['file']
        user_id = args['user_id']

        if uploaded_file:
            # Validate file extension
            if not self.file_service.is_valid_file(uploaded_file.filename):
                return {'message': 'Invalid file type. Only PDF and Word documents are allowed.'}, 400
            
            filepath = self.file_service.save_file(uploaded_file, user_id)
            print("file path saved: ",filepath)
            return {'message': 'File uploaded successfully', 'file_path': filepath}, 201
        else:
            return {'message': 'No file provided'}, 400