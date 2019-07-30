# bot for @rude_qa chat

## Setup and run

#### Setup virtual environment
```
virtualenv -p /usr/local/bin/python3.7 venv

source venv/bin/activate
```

#### Install project requirements
```
pip install -r requirements.txt
```
####Setup environment variables
```
cp .env.dist .env
```
Fill .env file with actual values

####Run project
```
python3 src/rudeboy_bot.py
```
