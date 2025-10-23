
---

# Dummy CAMARA API Backend
# Random change


## 🧩 Overview

This repository contains a **dummy backend** implementation of  **CAMARA API endpoints**, used for testing, experimentation or integration demos.

---

* Uses **Connexion** framework to automatically handle routing based on the provided **OpenAPI spec (`openapi.yaml`)**.
* Organizes logic into a modular **`controllers/`** directory for clean separation of API endpoints.
* Provides automatic Swagger UI documentation for easy testing of API endpoints.
* Loads configuration parameters from `.env` file.

**Directory structure:**

```
.
├── app.py
├── controllers/
|   |   experimental/ 
│   │   └── qod_controller.py
│   │   └── verify_controller.py
│   ├── v1/
│   │   └── example_controller.py
│   ├── v2/
│   │   └── example_controller.py
|   |   └── example_controller.py
├── openapi.yaml
├── .env
└── requirements.txt

```

---

## ⚙️ Installation

### Option 1

Follow these steps to set up and run the API locally.


```
git clone https://github.com/your-username/dummy-camara-backend.git
cd dummy-camara-backend
python3 -m venv venv (Tested with python versions 3.10x and 3.12x)
source venv/bin/activate    # On Windows: venv\Scripts\activate
pip install -r requirements.txt
Create a `.env` file in the project root (if not already present) and set your API configuration:
API_HOST=127.0.0.1
API_PORT=8081
```


## 🚀 Usage

### Option 1
```
python3 app.py
```


Once the server is running, open your browser and visit:

* **Swagger UI:** [http://127.0.0.1:8081/ui/](http://127.0.0.1:8081/ui/)
  to explore and test the endpoints interactively. 
  * The url may very in case of the corresponding environment variables

---

## 🤝 Contributing

To contribute:

1. **Fork** the repository.
2. **Create a new branch** for your feature or fix:

   ```bash
   git checkout -b feature/my-feature
   ```
3. **Commit** your changes:

   ```bash
   git commit -m "Add new endpoint for dummy CAMARA data"
   ```
4. **Push** your branch and open a **Pull Request**.

Please make sure to:

* Update or add OpenAPI definitions in `openapi.yaml` with additional API end-points.
* Create a new folder under `controllers/` (e.g., controllers/v3/).  
* Point each `operationId` to the new controller module.

---


