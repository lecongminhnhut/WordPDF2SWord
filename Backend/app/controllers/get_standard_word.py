from flask_restful import Resource, reqparse
from app.services.get_standard_word_service import GetStandardWordService

GET_STANDARD_WORD_ROUTE = '/get-standard-word'

class GetStandardWord(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('user_id', type=int, location='json', required=True, help='User ID is required') # not use
        self.parser.add_argument('file_path', type=str, location='json', required=False, help='Image path is required')
        self.service = GetStandardWordService()

    def post(self):
        args = self.parser.parse_args()
        user_id = args['user_id']
        file_path = args['file_path'] # already contain user_id inside the path

        print(f"User ID: {user_id}")
        print(len(file_path), file_path)

        return self.service.get_result(file_path)