# undocumented-aws-api-hunter

A tool to uncover, extract, and monitor undocumented AWS APIs from the AWS console. This tool was released at the the [fwd:cloudsec EU](https://fwdcloudsec.org/conference/europe/) talk, "[Hidden Among the Clouds: A Look at Undocumented AWS APIs](https://docs.google.com/presentation/d/1jJM_9KPfYZL60B56MQwQTym1H_A63abz2t_p_8Vo8MU/edit?usp=sharing)". This research has already uncovered some useful [tradecraft](https://frichetten.com/blog/undocumented-amplify-api-leak-account-id/), and even two [cross-tenant vulnerabilities](https://frichetten.com/blog/minor-cross-tenant-vulns-app-runner/), however due to the shear volume of undocumented APIs found there are likely many more. 

## Table of Contents

- [How does it work?](#how-does-it-work)
- [Usage](#usage)
- [Output](#output)
- [How to Build Docker Container](#how-to-build-docker-container)
- [Manual Installation/Usage](#manual-installationusage)
- [Scripts (generate stats)](#scripts-generate-stats)
  - [Undocumented parameters are only compared at top level](#undocumented-parameters-are-only-compared-at-top-level)
- [Author](#author)

## How does it work?

The undocumented-aws-api-hunter uses [Selenium](https://www.selenium.dev/) to pilot a headless instance of [Google Chrome](https://www.google.com/chrome/) and crawl the AWS console. It starts by signing into the console using an IAM user. Next, it will extract the service pages from the search bar of the console. It will then visit each of these pages and search the JavaScript being loaded on each page for AWS service models. Once it finds a model, it will store it.    

![364505916-476d7532-a6e4-491a-843c-33704819135b](https://github.com/user-attachments/assets/8133dd16-b41d-4610-a2c2-4ee3d9f9ab04)

undocumented-aws-api-hunter will deduplicate models and only store shapes, operations, and other information that is net-new. Subsequent runs of the undocumented API hunter can add new data to the extracted models. For an example extracted dataset, please see [here](https://github.com/frichetten/aws-api-models).

> [!WARNING]
> From some nominal testing it appears that this tool works on M series Macs, however be aware that because this tool uses [Selenium](https://www.selenium.dev/) and hence, [Google Chrome](https://www.google.com/chrome/), there may be some funkyness on non-x86-64 machines. If you'd like to run this in production it would be best to do so on an x86 Linux machine. 

## Usage

Please create an IAM user in your account with console access. Then create a `.env` with the following environment variables with the associated info: `UAH_USERNAME`, `UAH_PASSWORD`, and `UAH_ACCOUNT_ID`. With those variables set you can run the tool. This user must **NOT** have any permissions. If they have any IAM policies granting permissions it runs the risk of the automation accidentally invoking something.

Run the container with the following:

```
docker run -it --rm -v ${PWD}/models:/app/models -v ${PWD}/logs:/app/logs --env-file .env ghcr.io/datadog/undocumented-aws-api-hunter:latest
```

## Output

When running this tool a number of artifacts are created, including:

- Models: Models are output to `/models`. Each subsequent run of the tool should use the same model directory as the tool will deduplicate based on previous findings.
- Logs: Logs are output to `/logs/application.log`. This includes a running output of models, operations, and parameters found. This is particularly useful to monitor for new findings.
- Endpoints: AWS will often store endpoints in the HTML (yes, that is correct) of pages in the console. This tool will extract those and store them in a file called `endpoints.txt`. This can be useful for finding API endpoints for these undocumented APIs, however it is important to stress that this is not ALL endpoints. It may return a few hundred (when tens of thousands or more exist). If you're interested in finding more API endpoints, [this](https://securitylabs.datadoghq.com/articles/non-production-endpoints-as-an-attack-surface-in-aws/) method is recommended.

## How to Build Docker Container

```
git clone https://github.com/DataDog/undocumented-aws-api-hunter.git
```

Build the Docker container:

```
docker build -t undocumented-aws-api-hunter .
```

## Manual Installation/Usage

> [!IMPORTANT]  
> This is only neccessary if you'd like to help with development of the project. If you just want to use it you would be much better served with the Docker option above. 

```
git clone https://github.com/DataDog/undocumented-aws-api-hunter.git
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
./undocumented-aws-api-hunter.py --headless
```

## Scripts (generate stats)

Within this repo is a scripts directory which contains some scripts for generating stats on undocumented APIs. Each stat is split into its own section to make it easier to read. As a part of generating these stats there are some gotchas/limitations that are worth noting. They are described down below.

### Undocumented parameters are only compared at top level

In AWS API models, parameters for APIs are described as "shapes". These shapes are the format by which parameters are passed to the API. Shapes can be recursive, with one shape having multiple shapes within itself (they can even reference [themselves](https://github.com/boto/botocore/blob/bc89f1540e0cbb000561a72d20de9df0e92b9f4d/botocore/data/lexv2-runtime/2020-08-07/service-2.json#L532) which is fun to debug). When we compare these shapes between the botocore library and the extracted models we only compared shapes at the top level. This knowingly undercounts how many there are because down the chain there may be sub-shapes which have different fields. 

This undercounting is intentional because properly evaluating this is a problem to be solved. The reson is that AWS' own models are not descriptive enough to acomplish this. As an example `lambda-2015-03-32:UpdateFunctionEventInvokeConfig` has the shape DestinationConfig, this has a sub-shape OnSuccess, which itself has a member for "[Destination](https://github.com/Frichetten/aws-api-models/blob/4bc7b764593d2c2b78e3f81ff8c7027bd7048e50/models/lambda-2015-03-31-rest-json.json#L4358)".

In botocore all of this is still true, however it continues on. "Destination" has a sub-member for "[DestinationArn](https://github.com/boto/botocore/blob/0ac30565017f1486b2eebf9bd90b5411f0d7f1fb/botocore/data/lambda/2015-03-31/service-2.json#L4747)". 

![365281205-fa24b438-4f82-4571-9eeb-e96b4c89eb37](https://github.com/user-attachments/assets/ac98506a-38b2-49c8-af12-d2aa62774267)

It is not clear why the models are not the same. My working theory is that AWS uses a lot of code generation for it's models. As a result, models are often fragmented and don't always contain the full set. As a result, it's possible that we are not properly merging shapes and missing some parts of them. Regardless of the reason why, we are unable to further analyze shapes.

If you find a way to reliably (emphasis) do this, please let me know. I would love to hear about it. For now, we are only comparing the top level parameters. This has the knock-on effect of reporting fewer undocumented parameters than there actually are.

## Author

This tool was written by [Nick Frichette](https://frichetten.com/) in his free time. To find more of his research on AWS, please see [Datadog Security Labs](https://securitylabs.datadoghq.com/).

