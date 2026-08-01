from flask_restful import Api
from app.controllers.user import User, USER_ROUTE
from app.controllers.upload_file import UploadFile, UPLOAD_FILE_ROUTE
from app.controllers.get_file import GetFile, GET_FILE_ROUTE
from app.controllers.get_standard_word import GetStandardWord, GET_STANDARD_WORD_ROUTE
from app.controllers.delete_user import DeleteUser, DELETE_USER_ROUTE
from app.main.errors import errors

# Flask API Configuration
api = Api(
    catch_all_404s=True,
    errors=errors,
    # prefix='/api'
)

# api.add_resource(UserList, '/users')
# api.add_resource(User, '/users/<int:id>/')

api.add_resource(UploadFile, UPLOAD_FILE_ROUTE)
api.add_resource(GetFile, GET_FILE_ROUTE)
api.add_resource(GetStandardWord, GET_STANDARD_WORD_ROUTE)
api.add_resource(User, USER_ROUTE)
api.add_resource(DeleteUser, DELETE_USER_ROUTE)