import re, json, argparse, asyncio, aiohttp, colorama
from bs4 import BeautifulSoup
from lxml import etree
from colorama import Fore, Style

colorama.init(autoreset=True)

class AsyncWordPressScanner:

    def __init__(self, url, user_agent):
        self.url = str(url)
        self.user_agent = user_agent
        self.files = set()
        self.version = None
        self.users = []

    async def fetch(self, session, url):
        try:
            async with session.get(url, headers={'User-Agent': self.user_agent}) as response:
                if response.status == 200:
                    print(f"{Fore.CYAN}Fetching {url} - Status: {response.status}{Style.RESET_ALL}")
                    return await response.text()
                elif response.status == 404:
                    # Don't print anything for 404 errors
                    return None
                else:
                    print(f"{Fore.YELLOW}Failed to fetch {url}: Status {response.status}{Style.RESET_ALL}")
        except Exception as e:
            print(f'{Fore.RED}Error fetching {url}: {e}{Style.RESET_ALL}')
            return None

    async def check_wordpress(self, session):
        wordpress_files = [
            'wp-login.php',
            'wp-admin/',
            'wp-includes/',
            'wp-content/',
            'wp-json/wp/v2/'
        ]

        print(f"{Fore.GREEN}\nChecking if site is a WordPress site...{Style.RESET_ALL}")
        for path in wordpress_files:
            url = f"{self.url}/{path}"
            response = await self.fetch(session, url)
            if response:
                print(f'{Fore.GREEN}WordPress detected via: {url}{Style.RESET_ALL}')
                break
        else:
            print(f'{Fore.RED}Not a WordPress site.{Style.RESET_ALL}')
            return False

        response = await self.fetch(session, self.url)
        if response and '<meta name="generator" content="WordPress' in response:
            print(f'{Fore.GREEN}WordPress detected via meta tag.{Style.RESET_ALL}')
            return True

        print(f'{Fore.GREEN}WordPress detected via files and directories.{Style.RESET_ALL}')
        return True
    
    async def check_readme(self, session):
        response = await self.fetch(session, f'{self.url}/readme.html')
        if response:
            print(f'{Fore.GREEN}README file found at {self.url}/readme.html{Style.RESET_ALL}')
        else:
            print(f'{Fore.RED}No README file found.{Style.RESET_ALL}')

    async def check_debug_log(self, session):
        print(f"{Fore.GREEN}Checking for debug.log...{Style.RESET_ALL}")
        try:
            response = await self.fetch(session, f'{self.url}/debug.log')
            if response is not None:
                if '404' in response:
                    print(f'{Fore.RED}No debug log file found at {self.url}/debug.log (404 error){Style.RESET_ALL}')
                else:
                    print(f'{Fore.GREEN}Debug log file found at {self.url}/debug.log{Style.RESET_ALL}')
            else:
                print(f'{Fore.YELLOW}Failed to fetch {self.url}/debug.log: No response received.{Style.RESET_ALL}')
        except Exception as e:
            print(f'{Fore.RED}Error checking debug log: {e}{Style.RESET_ALL}')

    async def check_backup_file(self, session):
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
            'wp-config.php.TEST', "wp-config.php._INC", "wp-config_INC",
            'wp-config.local.php', 'wp-config.prod.php', 'wp-config.dev.php', 
            '.env', 'README.md', '.gitignore', 
        ]

        print(f"{Fore.GREEN}\nChecking for backup files...{Style.RESET_ALL}")
        backup_found = False

        for backup_file in backup_files:
            response = await self.fetch(session, f"{self.url}/{backup_file}")
            if response and response.status == 200:
                print(f'{Fore.GREEN}Backup file found at: {self.url}/{backup_file}{Style.RESET_ALL}')
                backup_found = True

        if not backup_found:
            print(f'{Fore.RED}No backup files found for {self.url}.{Style.RESET_ALL}')

    async def check_directory_listing(self, session):
        directories = ['wp-content/uploads/', 'wp-content/plugins/', 'wp-content/themes/', 'wp-includes/', 'wp-admin/']
        dir_names = ['Uploads', 'Plugins', 'Themes', 'Includes', 'Admin']

        for directory, name in zip(directories, dir_names):
            response = await self.fetch(session, self.url + '/' + directory)
            if response and 'Index of' in response:
                self.files.add(directory)
                print(f'{name} directory has directory listing enabled at {self.url + "/" + directory}')

    async def is_xml_rpc(self, session):
        print(f'\nChecking xmlrpc.php on {self.url}')
        url = f'{self.url}/xmlrpc.php'
        response = await self.fetch(session, url)
        
        if response is not None:
            print(f'XML-RPC Interface available under: {url}')
        else:
            print(f'Failed to fetch XML-RPC interface at: {url}')

        try:
            async with session.get(url, headers={'User-Agent': self.user_agent}) as resp:
                if resp.status == 200:
                    print(f'XML-RPC Interface accessible at: {url}')
                elif resp.status == 404:
                    print('XML-RPC interface is not available (404 error).')
                else:
                    print(f'XML-RPC interface inaccessible (Status: {resp.status}).')
        except Exception as e:
            print(f'Error checking XML-RPC status: {e}')

    async def check_robots_text(self, session):
        response = await self.fetch(session, f'{self.url}/robots.txt')
        if response:
            print(f'robots.txt available under: {self.url}/robots.txt')
            lines = response.split('\n')
            for l in lines:
                if 'Disallow:' in l:
                    print(f'Interesting entry from robots.txt: {l}')

    async def check_full_path_disclosure(self, session):
        response = await self.fetch(session, self.url + '/wp-includes/rss-functions.php')
        if response:
            regex = re.compile('Fatal error:.*? in (.*?) on', re.S)
            matches = regex.findall(response)

            if matches:
                exposed_path = matches[0].replace('\n', '').strip()
                print(f'Full Path Disclosure (FPD) in {self.url + 'wp-includes/rss-functions.php'}')
                print(f'Exposed Path: {exposed_path}')

    async def enum_wordpress_users(self, session):
        response = await self.fetch(session, f'{self.url}/wp-json/wp/v2/users')
        if response:
            print('Enumerating WordPress users')
            users = json.loads(response)
            for user in users:
                print(f'Identified the following user: {user["id"]}, {user["name"]}, {user["slug"]}')
            self.users = users


    async def extract_version(self, response):
        match = re.search(r'Version ([0-9]+\.[0-9]+\.?[0-9]*)', response)
        if match:
            return match.group(1)
        print('WordPress version not found in the response.')

    async def crawl_sitemap_for_forms(self, session, processed_urls=None):
        if processed_urls is None:
            processed_urls = set()

        robots_url = self.url + '/robots.txt'
        response = await self.fetch(session, robots_url)

        if response:
            sitemap_url = None  
            lines = response.split('\n')

            for line in lines:
                if line.strip().startswith('Sitemap:'):
                    sitemap_url = line.split(':', 1)[1].strip()
                    break

            if sitemap_url and sitemap_url not in processed_urls:
                processed_urls.add(sitemap_url)
                response = await self.fetch(session, sitemap_url)

                if response:
                    sitemap_xml = etree.fromstring(response.encode('utf-8'))
                    loc_elements = sitemap_xml.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                    urls = [loc.text for loc in loc_elements]

                    forms_with_input = []

                    for sitemap_url in urls:
                        if sitemap_url not in processed_urls:
                            processed_urls.add(sitemap_url)
                            response = await self.fetch(session, sitemap_url)

                            if response:
                                page_soup = BeautifulSoup(response, features='lxml')
                                forms = page_soup.find_all('form')

                                for form in forms:
                                    if form.find('input', {'type': 'text'}):
                                        forms_with_input.append(sitemap_url)
                                        break  

                    for sitemap_url in urls:
                        if sitemap_url.endswith('.xml'):
                            nested_forms = await self.crawl_sitemap_for_forms(session, processed_urls)
                            forms_with_input.extend(nested_forms)

                    return forms_with_input
                else:
                    print(f'Failed to fetch sitemap URL {sitemap_url}.')
            else:
                print(f'Sitemap URL {sitemap_url} has already been processed or is not found.')
        else:
            print(f'Failed to fetch robots.txt from {robots_url}.')

        return []
    
    async def check_plugins(self, session):
        plugin_directory_url = f'{self.url}/wp-content/plugins/'
        rest_api_plugins_url = f'{self.url}/wp-json/plugins/v1/all'
        known_plugins = [
            'wordpress-seo/wp-seo.php',  # Yoast SEO
            'akismet/akismet.php',        # Akismet
            'woocommerce/woocommerce.php', # WooCommerce
        ]

        response = await self.fetch(session, plugin_directory_url)
        if response and "Index of" in response:
            print(f'Plugin directory listing found at {plugin_directory_url}')

        response = await self.fetch(session, rest_api_plugins_url)
        if response:
            try:
                plugins = json.loads(response)
                print('Installed Plugins from REST API:')
                for plugin in plugins:
                    print(f'{plugin['name']} - {plugin['version']}')
            except json.JSONDecodeError:
                print('Failed to decode JSON response from the REST API.')

        for plugin in known_plugins:
            plugin_url = f'{self.url}/wp-content/plugins/{plugin}'
            response = await self.fetch(session, plugin_url)
            if response:
                print(f'Known plugin found: {plugin}')

    async def scan(self, checks):
        async with aiohttp.ClientSession() as session:
            tasks = []

            check_methods = {
                'wordpress': self.check_wordpress,
                'readme': self.check_readme,
                'debug-log': self.check_debug_log,
                'backup-file': self.check_backup_file,
                'directory-listing': self.check_directory_listing,
                'xml-rpc': self.is_xml_rpc,
                'robots-text': self.check_robots_text,
                'full-path-disclosure': self.check_full_path_disclosure,
                'enum-users': self.enum_wordpress_users,
                'sitemap-forms': self.crawl_sitemap_for_forms,
                'check-plugins': self.check_plugins,
            }

            for check in checks:
                if check in check_methods:
                    tasks.append(check_methods[check](session))

            await asyncio.gather(*tasks)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='WordPress Scanner')
    parser.add_argument('url', help='The URL of the WordPress site to scan')
    parser.add_argument('--user-agent', default='Wordpresscan - For educational purpose only!', help='User agent to use')
    parser.add_argument('--checks', default='wordpress', help='Comma-separated list of checks to perform: wordpress, readme, debug-log, backup-file, directory-listing, xml-rpc, robots-text, full-path-disclosure, enum-users, sitemap-forms, check-plugins')

    args = parser.parse_args()
    checks = args.checks.split(',')

    scanner = AsyncWordPressScanner(args.url, args.user_agent)
    asyncio.run(scanner.scan(checks))
