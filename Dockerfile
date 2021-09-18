FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./discord-mensa.py" ]

# $ docker build -t discord-mensa .
# $ docker run -it --rm --name discord-mensa-running discord-mensa