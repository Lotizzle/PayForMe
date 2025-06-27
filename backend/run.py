import os
import sys

from dotenv import load_dotenv

load_dotenv()

# Add the project root directory to Python's module search path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("Current working directory:", os.getcwd())
print("Python path:", sys.path)
print("Contents of app directory:", os.listdir("app"))
print("Contents of app/utils directory:", os.listdir("app/utils"))

from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)