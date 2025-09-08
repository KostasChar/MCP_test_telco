import connexion

# In-memory stores
qod_sessions = {}

def create_app():
    app = connexion.App(__name__, specification_dir=".")
    app.add_api(
        "openapi.yaml",
        strict_validation=True,
        validate_responses=True,
        swagger_ui=True  # enable Swagger UI explicitly
    )
    return app


if __name__ == "__main__":
    cnx_app = create_app()
    # This runs the underlying Flask app
    cnx_app.run(host="0.0.0.0", port=5000)
