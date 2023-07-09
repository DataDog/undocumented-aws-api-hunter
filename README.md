# undocumented-api-hunter

A tool to uncover undocumented apis from the AWS Console.

## Installation

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

Run the tool with:

```
./undocumented-api-hunter.py --headless
```
