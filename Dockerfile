FROM python:3.11

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

RUN apt update
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt install -y ./google-chrome-stable_current_amd64.deb

RUN CHROMEDRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE` && \
	mkdir ./chromedriver && \
	cd ./chromedriver && \
	wget https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip && \
	unzip chromedriver_linux64.zip && \
	chmod +x chromedriver && \
	mv chromedriver /usr/bin/chromedriver

CMD ["python", "./undocumented-api-hunter.py", "--headless"]
