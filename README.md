# WordPress Scanner

A Python script for scanning WordPress websites to identify vulnerabilities and potential issues. This tool checks various aspects of a WordPress site, including version detection, common files, directory listings, debug logs, backup files, exposed paths, XML-RPC interfaces, and more.


## Requirements
```
pip install -r requirements.txt
```

## Usage
```
usage: wp.py [-h] [--user-agent USER_AGENT] [--nocheck] url

Options:
  <URL>             The URL of the WordPress site to scan.
  --user-agent      (Optional) Specify a custom User-Agent header for the requests.
  --nocheck         (Optional) Skip the WordPress detection check.
```
The script will analyze the provided WordPress site and report its findings, such as detected     plugins, exposed paths, users, and more.
