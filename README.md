# PROJECT MOON - Gsync Simulator

A web-based gyrosynchrotron emission spectrum simulator for solar flares.

## 🚀 How to Run

### Quick Start with Docker (Recommended)
If you have Docker installed, you can run the entire application with a single command:

```bash
docker-compose up --build
```

- The **Backend API** will be available at `http://localhost:8000`.
- The **Frontend** will be available at `http://localhost:8080`.

To stop the application, press `Ctrl+C` or run:
```bash
docker-compose down
```

### Manual Setup
To run this project manually on a new computer, follow these steps:

### 1. Prerequisites
Ensure you have **Python 3.8 or newer** installed on your system.

### 2. Setup Environment
Open your terminal in the project directory and run:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Backend API
Start the FastAPI server:

```bash
python api.py
```
The server will start at `http://localhost:8000`.

### 4. Run the Frontend
You can serve the frontend using any local server, or simply open `index.html` in your browser.

Using Python to serve the frontend:
```bash
python -m http.server 8080
```
Then open `http://localhost:8080` in your browser.

### 5. Testing APIs with Bruno
We recommend using **[Bruno](https://www.usebruno.com/)**, a fast and open-source API client, to test the endpoints.

1. **Download Bruno**: [https://www.usebruno.com/downloads](https://www.usebruno.com/downloads)
2. **Open Collection**: In Bruno, click on **"Open Collection"** and select the `api_doc/` folder in this repository.
3. **Test Endpoints**: You can now see and run all the available API requests.

## ⚙️ Features
- **Simulation**: Model gyrosynchrotron emission using two modes:
  - **INITIALIZE SIMULATION**: Uses the high-performance compiled extension (may require compilation on non-macOS/non-Python 3.9 systems).
  - **INITIALIZE SIMULATION (PYTHON) BETA**: Uses a pure Python implementation that works on any platform.
- **Import/Export Settings**: Save and load your configurations as JSON files.
- **Data Import**: Upload `.dat` files with frequency and flux data.
- **Export Results**: Download a `.zip` file containing the simulation plot and the calculated spectrum.

## 🛠 Compilation (Optional)
If you wish to use the high-performance Fortran version on a system other than macOS (Python 3.9), you will need a Fortran compiler and `f2py` (comes with NumPy). Run the following in the `gsync/` folder:

```bash
f2py -c gyro.f -m gyro
```
