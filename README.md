# undocumented-api-hunter

A tool to uncover, extract, and monitor undocumented AWS APIs from the AWS console.

## How does it work?

The undocumented-api-hunter uses [Selenium](https://www.selenium.dev/) to pilot a headless instance of [Google Chrome](https://www.google.com/chrome/) and crawl the AWS console. It starts by signing into the console using an IAM user. Next, it will extract the service pages from the search bar of the console. It will then visit each of these pages and search the JavaScript being loaded on each page for AWS service models. Once it finds a model, it will store it.    

![fwdcloudsec EU 2024 - Hidden Among the Clouds_ A Look at Undocumented AWS APIs](https://github.com/user-attachments/assets/476d7532-a6e4-491a-843c-33704819135b)

undocumented-api-hunter will deduplicate models and only store shapes, operations, and other information that is net-new. Subsequent runs of the undocumented API hunter can add new data to the extracted models. For an example extracted dataset, please see [here](https://github.com/frichetten/aws-api-models).

> [!WARNING]
> From some nominal testing it appears that this tool works on M series Macs, however be aware that because this tool uses [Selenium](https://www.selenium.dev/) and hence, [Google Chrome](https://www.google.com/chrome/), there may be some funkyness on non-x86-64 machines. If you'd like to run this in production it would be best to do so on an x86 Linux machine. 

## Docker Install/Usage

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

> [!IMPORTANT]  
> This is only neccessary if you'd like to help with development of the project. If you just want to use it you would be much better served with the Docker option above. 

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
