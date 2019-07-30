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
#### Setup environment variables
```
cp .env.dist .env
```
Fill .env file with actual values

#### Run project
```
python3 src/rudeboy_bot.py
```
## Run in Docker

#### Build image
```
docker build . -t rudeboy
```
#### Setup environment variables
```
cp .env.dist .env
```
Fill .env file with actual values

#### Run container
```
docker-compose -f docker-compose.yml up
```
or for detached mode
```
docker-compose -f docker-compose.yml up -d
```
