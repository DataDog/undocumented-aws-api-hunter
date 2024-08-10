# undocumented-api-hunter

A tool to uncover undocumented apis from the AWS Console.

## Docker Install/Usage

> [!WARNING]
> Because this tool uses [Selenium](https://www.selenium.dev/) and hence, [Google Chrome](https://www.google.com/chrome/), it is only functional from an x86-64 machine. It will **not** work on an M series Mac. Being in a Docker container does not change this. 

```
git clone https://github.com/Frichetten/undocumented-api-hunter.git
```

Build the Docker container:

```
docker build -t undocumented-api-hunter .
```

Please create an IAM user in your account with console access. Then create a `.env` with the following environment variables with the associated info: `UAH_USERNAME`, `UAH_PASSWORD`, and `UAH_ACCOUNT_ID`. With those variables set you can run the tool. This user must **NOT** have any permissions. If they have any IAM policies granting permissions it runs the risk of the automation accidentally invoking something.

Run the container with the following:

```
docker run -it --rm -v ${PWD}/models:/app/models -v ${PWD}/logs:/app/logs --env-file .env undocumented-api-hunter
```

## Manual Installation/Usage

```
git clone https://github.com/Frichetten/undocumented-api-hunter.git
```

Inside the directory, create a new [virtual environment](https://docs.python.org/3/library/venv.html) with the following command:

```
python3 -m venv ./venv
```

Activate it:

```
source ./venv/bin/activate
```

Install packages:

```
python3 -m pip install -r requirements.txt
```

Install the [ChromeDriver](https://chromedriver.chromium.org/downloads) for your operating system. This is required for Selenium. The process for this will depend on your OS so I will keep it vague. I used parts of [this](https://tecadmin.net/setup-selenium-chromedriver-on-ubuntu/) guide (once you have `chromedriver` installed you can stop. No need to complete the other steps) for a Linux machine.

Please create an IAM user in your account with console access. Then export the following environment variables with the associated info: `UAH_USERNAME`, `UAH_PASSWORD`, and `UAH_ACCOUNT_ID`. With those variables set you can run the tool. This user must **NOT** have any permissions. If they have any IAM policies granting permissions it runs the risk of the automation accidentally invoking something.

```
./undocumented-api-hunter.py --headless
```
