# Projeto Granja Backend

## Overview
Projeto Granja is a web application designed to manage and facilitate various functionalities related to a farming project. This backend project is built using Flask, a lightweight WSGI web application framework in Python.

## Project Structure
```
projeto-granja-backend
├── app
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── controllers.py
│   └── config.py
├── requirements.txt
├── .env
└── README.md
```

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd projeto-granja-backend
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**
   Create a `.env` file in the root directory and add your environment-specific variables, such as:
   ```
   SECRET_KEY=your_secret_key
   DATABASE_URL=your_database_url
   ```

5. **Run the Application**
   ```bash
   flask run
   ```

## Usage
Once the application is running, you can access the API endpoints defined in `app/routes.py`. Use tools like Postman or curl to interact with the API.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.# sistema-granja
