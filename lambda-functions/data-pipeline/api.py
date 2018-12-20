import json
from flask import Flask, Blueprint, jsonify
from flask import request
from flask import abort

import download

app = Flask(__name__)
errors = Blueprint('errors', __name__)

@errors.app_errorhandler(Exception)
def handle_error(error):
    message = [str(x) for x in error.args]
    status_code = 500
    success = False
    print(request.url)
    response = {
        'success': success,
        'error': {
            'type': error.__class__.__name__,
            'message': message
        },
        'request': request.get_json()
    }

    return jsonify(response), status_code

app.register_blueprint(errors)

@app.route('/helloworld')
def hello():
    response = {
        "statusCode": 200,
        "body": "hi"
    }
    id = request.args.get('id')

    return f"Hi {id}!"

    # Use this code if you don't use the http event with the LAMBDA-PROXY
    # integration
    """
    return {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "event": event
    }
    """
@app.route('/cropped_download/', methods=["POST"])
def cropped_download():

    image_ids = request.form.getlist('image_id')
    polygon = request.form.get('polygon')
    bucket = request.form.get('bucket')

    if(image_ids is None or polygon is None or bucket is None):
        raise ValueError("Missing argument.")



    return (download.cropped_download(image_ids, polygon, bucket))

from flask import Blueprint, jsonify
