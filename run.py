from app import create_app

if __name__ == '__main__':
    try:
        print("Criando aplicação...")
        app = create_app()
        print("Aplicação criada com sucesso!")
        
        print("Iniciando servidor...")
        app.run(
            host='127.0.0.1',
            port=5005,
            debug=True,
            use_reloader=False 
        )
    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        traceback.print_exc()