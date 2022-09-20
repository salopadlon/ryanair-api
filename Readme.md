## Install dependencies

The project uses Python 3.8

Run this command to install all required packages

`pip install -r requirements.txt`

## Run application

To run the application use the following command from the directory of `main.py`


`uvicorn main:app --reload`

The application will by default run on address http://127.0.0.1:8000

## Using the application

To use the application select origin and destination airport and starting and ending period to list flight prices. 
After pressing the Search button, graph with tickets prices will show up. 