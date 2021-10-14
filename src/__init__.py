from flask import Flask  # import main Flask class and request object
from pathlib import Path

app = Flask(__name__)  # create the Flask app
# app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
# app.config['CACHE_DEFAULT_TIMEOUT'] = 0
app.config['DEBUG'] = True          # some Flask specific configs
# app.config['CACHE_TYPE'] = "simple"
