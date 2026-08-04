from threading import Lock

from flask_restful import Resource, reqparse
from app.services.get_standard_word_service import GetStandardWordService
from app.services.convert_pdf_to_word_service import PdfHasNoTextLayerError
from app.services.gemini_service import GeminiRateLimitError

GET_STANDARD_WORD_ROUTE = '/get-standard-word'
PROCESSING_LOCK = Lock()

class GetStandardWord(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('user_id', type=int, location='json', required=True, help='User ID is required') # not use
        self.parser.add_argument('file_path', type=str, location='json', required=False, help='Image path is required')
        self.service = GetStandardWordService()

    def post(self):
        lock_acquired = False
        try:
            args = self.parser.parse_args()
            user_id = args['user_id']
            file_path = args['file_path'] # already contain user_id inside the path

            lock_acquired = PROCESSING_LOCK.acquire(blocking=False)
            if not lock_acquired:
                return {
                    'message': (
                        'Backend đang xử lý một tài liệu khác. '
                        'Vui lòng thử lại sau khoảng 30 giây.'
                    )
                }, 503, {'Retry-After': '30'}

            return self.service.get_result(file_path)
        except PdfHasNoTextLayerError as exc:
            return {'message': str(exc)}, 422
        except GeminiRateLimitError as exc:
            return {'message': str(exc)}, 429
        except TimeoutError as exc:
            return {'message': str(exc)}, 504
        except Exception as exc:
            return {'message': f'Không thể xử lý tài liệu: {exc}'}, 500
        finally:
            if lock_acquired:
                PROCESSING_LOCK.release()
