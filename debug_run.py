print("=== INICIANDO DEBUG ===")

try:
    print("1. Importando Flask...")
    from flask import Flask, redirect, url_for
    print("   ✅ Flask importado!")

    print("2. Importando create_app...")
    from app import create_app
    print("   ✅ create_app importado!")

    print("3. Criando aplicação...")
    app = create_app()
    print("   ✅ Aplicação criada!")

    print("4. Iniciando servidor...")
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)

except ImportError as e:
    print(f"   ❌ ERRO DE IMPORT: {e}")
except Exception as e:
    print(f"   ❌ ERRO GERAL: {e}")
    import traceback
    traceback.print_exc()