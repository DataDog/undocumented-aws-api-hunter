FROM python:3.11

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

RUN apt update

# Find the latest Chrome deb here: https://pkgs.org/download/google-chrome-stable
RUN wget -q https://dl.google.com/linux/deb/pool/main/g/google-chrome-stable/google-chrome-stable_131.0.6778.69-1_amd64.deb
RUN apt install -y ./google-chrome-stable_131.0.6778.69-1_amd64.deb

RUN CHROMEDRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE` && \
	mkdir ./chromedriver && \
	cd ./chromedriver && \
	wget https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/131.0.6778.69/linux64/chromedriver-linux64.zip && \
	unzip chromedriver-linux64.zip && \
	cd chromedriver-linux64 && \
	chmod +x chromedriver && \
	mv chromedriver /usr/bin/chromedriver

RUN useradd -m -u 1000 user

USER user

CMD ["python", "./undocumented-aws-api-hunter.py", "--headless"]