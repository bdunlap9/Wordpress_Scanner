import requests, re, json, argparse

from bs4 import BeautifulSoup
from bs4.element import Comment
from lxml import etree

class WordPressScanner:
    def __init__(self, url, user_agent, nocheck):
        self.url = url
        self.user_agent = user_agent
        self.nocheck = nocheck
        self.files = set()

    def scan(self):
        self.check_wordpress()
        self.check_url()
        self.check_readme()
        self.check_debug_log()
        self.check_backup_file()
        self.check_directory_listing()
        self.check_robots_text()
        self.check_full_path_disclosure()
        website_content = self.get_website_content()  # Fetch the website content
        self.detect_wordpress_plugins(website_content)  # Pass the content to the detection function
        self.enum_wordpress_users()
        self.is_xml_rpc()
        self.is_debug_log()
        
        sitemap_url = self.url  # Define the sitemap URL
        processed_urls = set()  # Initialize a set for processed URLs
        forms_with_input = self.crawl_sitemap_for_forms(sitemap_url, processed_urls)

        if forms_with_input:
            print("URLs with input forms:")
            for url in forms_with_input:
                print(f'    {url}')
        else:
            print("No URLs with input forms found.")

    def check_wordpress(self):
        response = requests.get(self.url, verify=True)  # Verify the SSL certificate
        if self.nocheck and not "wp-" in response.text:
            print("Not a WordPress site.")
            exit()

    def crawl_sitemap_for_forms(self, url, processed_urls=None):
        if processed_urls is None:
            processed_urls = set()

        try:
            # Construct the robots.txt URL by appending '/robots.txt'
            robots_url = self.url + '/robots.txt'
            response = requests.get(robots_url)

            if response.status_code == 200:
                sitemap_url = None  # Initialize sitemap URL
                lines = response.text.split('\n')

                # Find the line containing 'Sitemap:'
                for line in lines:
                    if line.strip().startswith('Sitemap:'):
                        sitemap_url = line.split(':', 1)[1].strip()
                        break

                if sitemap_url:
                    if sitemap_url not in processed_urls:
                        processed_urls.add(sitemap_url)  # Add the sitemap URL to processed URLs
                        response = requests.get(sitemap_url)

                        if response.status_code == 200:
                            # Parse the sitemap as XML using lxml
                            sitemap_xml = etree.fromstring(response.content)
                            loc_elements = sitemap_xml.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
                            urls = [loc.text for loc in loc_elements]

                            forms_with_input = []

                            for sitemap_url in urls:
                                if sitemap_url not in processed_urls:
                                    processed_urls.add(sitemap_url)  # Add the URL to processed URLs
                                    response = requests.get(sitemap_url)

                                    if response.status_code == 200:
                                        page_content = response.text
                                        page_soup = BeautifulSoup(page_content, features="lxml")  # Parse as XML
                                        forms = page_soup.find_all("form")

                                        for form in forms:
                                            if form.find("input", {"type": "text"}):
                                                forms_with_input.append(sitemap_url)
                                                break  # No need to check other forms on the same page

                            # Recursively process XML files
                            for sitemap_url in urls:
                                if sitemap_url.endswith(".xml"):
                                    self.crawl_sitemap_for_forms(sitemap_url, processed_urls)

                            return forms_with_input
                        else:
                            print(f"Failed to fetch sitemap URL {sitemap_url}. Status code: {response.status_code}")
                    else:
                        print(f"Sitemap URL {sitemap_url} has already been processed.")
                else:
                    print("No sitemap URL found in robots.txt.")
            else:
                print(f"Failed to fetch robots.txt from {robots_url}. Status code: {response.status_code}")
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        return []

    def get_website_content(self):
        # Fetch the HTML content of the website using requests
        response = requests.get(self.url, verify=True)  # Verify the SSL certificate
        if "200" in str(response):
            return response.text

    def detect_wordpress_plugins(self, website_content):
        html_content = website_content
        soup = BeautifulSoup(html_content, 'lxml')

        # Look for meta tags related to plugins
        meta_tags = soup.find_all('meta', attrs={'name': 'wp-plugin'})
        if meta_tags:
            for tag in meta_tags:
                print("Found WordPress plugin meta tag:", tag['content'])

        # Search for comments in HTML
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            print("Found WordPress plugin comment:", comment)

        # Analyze script and link tags
        script_tags = soup.find_all(['script', 'link'])
        for tag in script_tags:
            if 'wp-content/plugins/' in tag.get('src', '') or 'wp-content/themes/' in tag.get('href', ''):
                tag_type = "Script" if tag.name == 'script' else "Stylesheet"
                tag_url = tag.get('src', '') if tag.name == 'script' else tag.get('href', '')
                print(f"Possible plugin-related {tag_type} found:")
                print(f"    URL: {tag_url}")
                print(f"    Type: {tag_type}")

    def is_debug_log(self):
        debug_log_url = self.url + '/debug.log'
        response = requests.get(debug_log_url, headers={"User-Agent": self.user_agent}, verify=True)
    
        if response.status_code == 200:
            if "404" not in response.text:
                self.files.add('debug.log')
                print(f"Debug log file found: {debug_log_url}")
        else:
            print(f"Debug log file not found at: {debug_log_url}")

    def check_url(self):
        print(f"URL     : {self.url}")
        response = requests.get(self.url, verify=True)  # Verify the SSL certificate
        if "200" in str(response):
            self.version = self.extract_version(response.text)
            print(f"Version : {self.version}")

    def check_readme(self):
        response = requests.get(self.url + '/readme.html', verify=True)  # Verify the SSL certificate
        if "200" in str(response):
            print(f"Readme file found at {self.url}readme.html")

    def check_debug_log(self):
        response = requests.get(self.url + '/debug.log', verify=True)  # Verify the SSL certificate
        if "200" in str(response) and "404" not in response.text:
            print(f"Debug log file found at {self.url}debug.log")

    def check_backup_file(self):
        backup_files = [
            'wp-config.php~', 'wp-config.php.save', '.wp-config.php.bck', 
            'wp-config.php.bck', '.wp-config.php.swp', 'wp-config.php.swp', 
            'wp-config.php.swo', 'wp-config.php_bak', 'wp-config.bak', 
            'wp-config.php.bak', 'wp-config.save', 'wp-config.old', 
            'wp-config.php.old', 'wp-config.php.orig', 'wp-config.orig', 
            'wp-config.php.original', 'wp-config.original', 'wp-config.txt', 
            'wp-config.php.txt', 'wp-config.backup', 'wp-config.php.backup', 
            'wp-config.copy', 'wp-config.php.copy', 'wp-config.tmp', 
            'wp-config.php.tmp', 'wp-config.zip', 'wp-config.php.zip', 
            'wp-config.db', 'wp-config.php.db', 'wp-config.dat',
            'wp-config.php.dat', 'wp-config.tar.gz', 'wp-config.php.tar.gz', 
            'wp-config.back', 'wp-config.php.back', 'wp-config.test', 
            'wp-config.php.test', "wp-config.php.1","wp-config.php.2",
            "wp-config.php.3", "wp-config.php._inc", "wp-config_inc",
            
            'wp-config.php.SAVE', '.wp-config.php.BCK', 
            'wp-config.php.BCK', '.wp-config.php.SWP', 'wp-config.php.SWP', 
            'wp-config.php.SWO', 'wp-config.php_BAK', 'wp-config.BAK', 
            'wp-config.php.BAK', 'wp-config.SAVE', 'wp-config.OLD', 
            'wp-config.php.OLD', 'wp-config.php.ORIG', 'wp-config.ORIG', 
            'wp-config.php.ORIGINAL', 'wp-config.ORIGINAL', 'wp-config.TXT', 
            'wp-config.php.TXT', 'wp-config.BACKUP', 'wp-config.php.BACKUP', 
            'wp-config.COPY', 'wp-config.php.COPY', 'wp-config.TMP', 
            'wp-config.php.TMP', 'wp-config.ZIP', 'wp-config.php.ZIP', 
            'wp-config.DB', 'wp-config.php.DB', 'wp-config.DAT',
            'wp-config.php.DAT', 'wp-config.TAR.GZ', 'wp-config.php.TAR.GZ', 
            'wp-config.BACK', 'wp-config.php.BACK', 'wp-config.TEST', 
            'wp-config.php.TEST', "wp-config.php._INC", "wp-config_INC"
        ]

        for backup_file in backup_files:
            response = requests.get(self.url + '/' + backup_file, headers={"User-Agent": self.user_agent}, verify=True)
            
            if response.status_code == 200:
                print(f"A backup file has been found at {self.url + backup_file}")

    def check_directory_listing(self):
        directories = ["wp-content/uploads/", "wp-content/plugins/", "wp-content/themes/","wp-includes/", "wp-admin/"]
        dir_name    = ["Uploads", "Plugins", "Themes", "Includes", "Admin"]

        for directory, name in zip(directories, dir_name):
            response = requests.get(self.url + '/' + directory, verify=True)  # Verify the SSL certificate
            if "Index of" in response.text:
                self.files.add(directory)
                print(f"{name} directory has directory listing enabled at {self.url + directory}")

    def is_xml_rpc(self):
        r = requests.get(self.url + "/xmlrpc.php", headers={"User-Agent": self.user_agent}, verify=True)
        if r.status_code == 405:
            self.files.add("xmlrpc.php")
            print(f"XML-RPC Interface available under: {self.url}xmlrpc.php")


    def check_robots_text(self):
        response = requests.get(self.url + "/robots.txt", verify=True)  # Verify the SSL certificate
        
        if response.status_code == 200:
            self.files.add("robots.txt")
            print(f"robots.txt available under: {self.url}robots.txt")
            lines = response.text.split('\n')
        
            for l in lines:
                if "Disallow:" in l:
                    print(f"Interesting entry from robots.txt: {l}")

    def check_full_path_disclosure(self):
        response = requests.get(self.url + "/wp-includes/rss-functions.php", verify=True)  # Verify the SSL certificate
        text = response.text
        regex = re.compile("Fatal error:.*? in (.*?) on", re.S)
        matches = regex.findall(text)

        if matches:
            # Extract the exposed path from the match
            exposed_path = matches[0].replace('\n', '').strip()

            print(f"Full Path Disclosure (FPD) in {self.url + 'wp-includes/rss-functions.php'}")
            print(f"Exposed Path: {exposed_path}")
    
    def enum_wordpress_users(self):
        response = requests.get(self.url + "/wp-json/wp/v2/users", headers={"User-Agent": self.user_agent}, verify=True)  # Verify the SSL certificate

        if "200" in str(response):
            print("Enumerating WordPress users")
            users = json.loads(response.text)
            for user in users:
                print(f"Identified the following user: {user['id']}, {user['name']}, {user['slug']}")
            self.users = users

    def extract_version(self):
        try:
            response = requests.get(self.url, verify=True)  # Verify the SSL certificate
        
            if response.status_code == 200:
                match = re.search(r'Version ([0-9]+\.[0-9]+\.?[0-9]*)', response.text)
                
                if match:
                    return match.group(1)
                else:
                    print("WordPress version not found in the response.")
            else:
                print(f"Failed to fetch content from {self.url}. Status code: {response.status_code}")
        except Exception as e:
            print(f"An error occurred while extracting WordPress version: {str(e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='WordPress Scanner')
    parser.add_argument('url', help='The URL of the WordPress site to scan')
    parser.add_argument('--user-agent', default='Wordpresscan - For educational purpose only !', help='User agent to use')
    parser.add_argument('--nocheck', action='store_true', help='Skip WordPress check')

    args = parser.parse_args()
    
    scanner = WordPressScanner(args.url, args.user_agent, args.nocheck)
    scanner.scan()
