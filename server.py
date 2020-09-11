# sasha 2020
from flask import Flask, render_template, request, redirect, jsonify
import pickle
import redis
import os
from flask_cors import CORS


r = redis.from_url(os.environ.get("REDIS_URL"))
app = Flask(__name__)
CORS(app)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/action', methods=['POST'])
def action():
    # Check the IP of the requester
    request_ip = request.remote_addr
    ips = request_ip.split('.')
    subnet = f'{ips[0]}.{ips[1]}.{ips[2]}.0'

    # Only change the mode if the IP is OK
    if subnet in ['127.0.0.0', '62.220.135.0', '192.168.130.0']:
        print(f'Changing to {request.form["mode"]}')

        mode = {'mode': request.form['mode']}
        p_mode = pickle.dumps(mode)
        r.set('mode', p_mode)

    return redirect('/', code=302)


@app.route('/status')
def status():
    # Pull data from redis and return as JSON
    p_mode = r.get('mode')
    mode = pickle.loads(p_mode)
    return jsonify(mode)


if __name__ == "__main__":
    # seed an initial value
    mode = {'mode': 'general'}
    p_mode = pickle.dumps(mode)
    r.set('mode', p_mode)

    # run server
    app.run(debug=False, host="0.0.0.0")
