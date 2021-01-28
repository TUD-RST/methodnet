# Deployment Information
## General

This directory contains a script and files to deploy the containing web application locally or at a fresh [uberspace](https://uberspace.de/) account.

We use [deploymentutils](https://codeberg.org/cknoll/deploymentutils) (which is built on top of  [fabric](https://www.fabfile.org/) (>=2.5). This decision seems to be a good compromise between raw bash scripts and a complex configuration management system like ansible – at least for python affine people.
Complete deployment should (at best) be a onliner.

## How to deploy `moodpoll` locally:

- Ensure you have this directory structure:

```
    [project_root]
    ├── [project_repo]/
    │   ├── .git/...
    │   ├── deployment/
    │   │   ├── README.md                  ← you read this file
    │   │   ├── deploy.py
    │   │   ├── general/...                ← general deployment files
    │   │   ├── uberspace/...              ← uberspace-specific deployment files
    │   │   └──  ...
    │   └── ...
    │
    ├── config.ini                         ← contains the project configuration (must be located outside the repo)
    ├── local_testing/                     ← will be auto-created by deploy.py
    └── ...
```

- run `python3 deploy.py local`
    - If you plan to play arround with the source files you can symlink them instead of copy use: `python3 deploy.py  -l local`. To get a full list of options (like omiting tests, omiting backup, ...) use `python3 deploy.py  -h`.
- go to `[project_root]/local_deployment/` and run `python3 manage.py runserver`
- note: if you want to deploy inside a virtual environment you have to manage that yourself


## Background

The local deployment directory is placed outside of \[project_repo\] to keep the repo directory clean. Thus, the repo-dir can still be used for development and for remote deployment. This structure also makes it easier to handle different secrets and fixtures for different usecases (local deployment, example content, testing, production).


## How to deploy  on a remote server ([uberspace](https://uberspace.de/)):

Note: We describe deployment on uberspace because from what we know it provides the lowest hurdle to test (and run) the webapp. Probably there are other equivalent or even better hosters out there.

### Preparation

Assumption: The deployment is run from a unix-like system. It is tested on Debian GNU/Linux, version 10.

- Create an [uberspace](https://uberspace.de)-account (first month is free), then pay what you like.
- Set up your ssh key in the webfrontend
- Locally run `pip install deployment_requirements.txt`
- Move `<project_root>/<project_repo>/deployment/config_example.ini` to `<project_root>/config.ini` and adapt the settings
- Change secret key

### Deployment

- Create an uberspace account and add you ssh-key (via webfrontend).
- Run `pip install deployment_requirements.txt`
- Have a look to `deploy.py` and so see what will be executed on your (remote) machine.
    - The script is mainly an automated version of this setup guide: <https://lab.uberspace.de/guide_django.html>.
- Run `eval $(ssh-agent); ssh-add -t 5m` to unlock you private ssh-key in this terminal (The deplyment script itself does not ask for your ssh-key password).
- Run `python3 deploy.py -h` to get an overview of available options
- Run `python3 deploy.py --initial remote`.
