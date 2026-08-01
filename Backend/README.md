1. Set Virtual environment
Install all project dependencies using:
```
$ pip install -r requirements.txt
```

2. In folder "Back end", create file `.env` containing the line:
```
GEMINI_API_KEY=""
```
(you can change the value of the key by your own)

3. Let the folder `dataset/` in folder `app/database/`. 

4. Let the folder `user/` in folder `app/database/`

5. Let the folder `files_upload/` in folder `app/database/`, so that the server could receive files uploaded by users.

6. Running
```
export FLASK_APP=app.py
python -m flask run
```

or you can run directly
```
flask run --host=0.0.0.0
```