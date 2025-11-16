import os
import connexion
from dotenv import load_dotenv


load_dotenv()
# Load environment variables with defaults

HOST = os.getenv("API_HOST", "127.0.0.1")
PORT = int(os.getenv("API_PORT", 8082))

# Create Connexion app
app = connexion.App(__name__, specification_dir="./")
app.add_api("openapi.yaml", strict_validation=True)

if __name__ == "__main__":
    print("Starting API server...")
    print(f"Swagger UI available at: http://{HOST}:{PORT}/ui/")
    # print(f"OpenAPI JSON available at: http://{HOST}:{PORT}/openapi.json")
    app.run(host=HOST, port=PORT)

