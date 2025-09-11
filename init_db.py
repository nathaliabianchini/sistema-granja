try:
    from app import create_app
    from app.models import db
    
    app = create_app()
    with app.app_context():
        db.create_all()
        print("Database initialized successfully!")

except Exception as e:
    print(f"ERRO: {e}")
    import traceback
    traceback.print_exc()
