# WordPress Scanner

A Python script for scanning WordPress websites to identify vulnerabilities and potential issues. This tool checks various aspects of a WordPress site, including version detection, common files, directory listings, debug logs, backup files, exposed paths, XML-RPC interfaces, and more.

## Usage

To use the WordPress Scanner, you'll need Python 3 and the following Python packages:

- `requests`
- `re`
- `json`
- `argparse`
- `BeautifulSoup`
- `lxml`

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/wordpress-scanner.git
   cd wordpress-scanner


2. Run the scanner with the following command:
     python wordpress_scanner.py <URL> [--user-agent <USER_AGENT>] [--nocheck]
     <URL>: The URL of the WordPress site to scan.
     --user-agent <USER_AGENT>: (Optional) Specify a custom User-Agent header for the requests.
     --nocheck: (Optional) Skip the WordPress detection check.

   The script will analyze the provided WordPress site and report its findings, such as detected     plugins, exposed paths, users, and more.
```
