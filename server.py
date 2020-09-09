# sasha 2020
from flask import Flask, render_template, request, redirect
import pickle
import redis
import os


r = redis.from_url(os.environ.get("REDIS_URL"))
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/action', methods=['POST'])
def action():
    print(request.form['mode'])
    
    mode = {'mode': request.form['mode']}
    p_mode = pickle.dumps(mode)
    r.set('mode', p_mode)

    return redirect('/', code=302)


@app.route('/status')
def status():
    p_mode = r.get('mode')
    mode = pickle.loads(p_mode)
    return str(mode)


if __name__ == "__main__":
    app.run(debug=True)
