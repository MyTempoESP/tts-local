from flask import Flask, request
import subprocess

app = Flask(__name__)

@app.route('/')
def speak():
    text = request.args.get('text')
    if not text:
        return 'Missing "text" parameter', 400

    try:
        subprocess.Popen(['espeak-ng', "-v", "pt-br", text])
        return '', 204
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
