# sasha 2020
from flask import Flask, render_template, request, redirect, jsonify
import pickle
import redis
import os
from flask_cors import CORS


r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
app = Flask(__name__)
CORS(app)


def checkAccess(request):
    '''Checks if the user can make this change'''

    # Check the IP of the requester
    request_ip = request.remote_addr
    ips = request_ip.split('.')
    subnet = f'{ips[0]}.{ips[1]}.{ips[2]}.0'

    # Checks if the "ALLOWED_IPS" environment variable contains IPs,
    # if it does, then checks if requester IP is in the allowed
    # list. The env var should be a comma separated list, e.g.
    # ALLOWED_IPS = "127.0.0.1,123.123.123.123"
    allowed_ips = os.getenv("ALLOWED_IPS", "")

    if allowed_ips != "":
        ips = allowed_ips.split(',')

        if subnet in ips:
            return True # Return true if the user is in allowed list
        else:
            return False

    else:
        return True # Always return true if we do not have a list


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/action', methods=['POST'])
def action():
    # If user has access, let them change the mode
    if checkAccess(request) == True:
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


@app.route('/params', methods=['GET', 'POST'])
def params():
    # If user has access, let them change the mode
    if checkAccess(request) == True:
        if request.method == 'GET':
            p_mode = r.get('params')
            params = pickle.loads(p_mode)
            return jsonify(params)
    else:
        return 'access denied'


if __name__ == "__main__":
    # seed an initial value
    mode = {'mode': 'general'}
    p_mode = pickle.dumps(mode)
    r.set('mode', p_mode)
    r.set('params', p_mode) # hack

    # set up ssl
    #context = ('/home/pi/Music-LED/cert.crt', '/home/pi/Music-LED/cert.key')

    # run server
    #app.run(debug=True, host="0.0.0.0", port=443, ssl_context=context)
    app.run(debug=True, host="0.0.0.0")