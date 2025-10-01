from flask import Flask

app = Flask(__name__)

@app.route('/')
def test():
    return "TESTE FUNCIONANDO!"

if __name__ == '__main__':
    print("Iniciando servidor de teste...")
    app.run(host='127.0.0.1', port=5000, debug=False)