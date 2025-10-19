import connexion

# Create Connexion app
app = connexion.App(__name__, specification_dir="./")
app.add_api("openapi.yaml", strict_validation=True)

if __name__ == "__main__":
    print("Starting  API server...")
    print("Swagger UI available at: http://localhost:8080/ui/")
 #   print("OpenAPI JSON available at: http://localhost:8080/openapi.json")
    app.run(host="0.0.0.0", port=8080)
