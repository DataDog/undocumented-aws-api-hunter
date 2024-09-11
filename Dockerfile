FROM --platform=linux/amd64 python:3.11

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

RUN apt update
RUN wget -q https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_118.0.5993.70-1_amd64.deb
RUN apt install -y ./google-chrome-stable_118.0.5993.70-1_amd64.deb

RUN CHROMEDRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE` && \
	mkdir ./chromedriver && \
	cd ./chromedriver && \
	wget https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/118.0.5993.70/linux64/chromedriver-linux64.zip && \
	unzip chromedriver-linux64.zip && \
	cd chromedriver-linux64 && \
	chmod +x chromedriver && \
	mv chromedriver /usr/bin/chromedriver

CMD ["python", "./undocumented-aws-api-hunter.py", "--headless"]
