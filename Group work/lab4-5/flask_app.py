import json
from itertools import chain
from functools import wraps
from kafka import KafkaProducer

from flask import Flask, render_template, request, make_response, jsonify, Response

producer = KafkaProducer(bootstrap_servers=['localhost:9092'],
                         value_serializer=lambda m: 
                         json.dumps(m).encode('ascii'))

app = Flask(__name__)

def json_response(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        body, status_code = function(*args, **kwargs)
        response = make_response(jsonify(body), status_code)
        return response
    return wrapped

@app.route('/')
def trainURL():
    return render_template('train.html')

@app.route("/api/<dir_name>/<file_name>", methods=['PUT'])
@json_response
def upload_json(dir_name: str, file_name: str):
    #print(request.json['data'])
    producer.send('json-topic', {'excercise': request.json['data']})
    return {'message': 'OK'}, 200

'''
@app.route('/json-topic2')
def stream():
    def eventStream():
        yield "data: IT IS WORKING!!\n\n"
    return Response(eventStream(), mimetype="text/event-stream")
'''

if __name__ == '__main__':
    app.run(debug=True, port=5000) #host='0.0.0.0', 
