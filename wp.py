import re, json, argparse, asyncio, aiohttp, colorama, warnings
from bs4 import BeautifulSoup
from lxml import etree
from colorama import Fore, Style

warnings.filterwarnings("ignore", category=UserWarning, module='bs4')
colorama.init(autoreset=True)

class AsyncWordPressScanner:

    def __init__(self, url, user_agent):
        self.url = str(url)
        self.user_agent = user_agent
        self.files = set()
        self.version = None
        self.users = []
    
    async def fetch(self, session, url, retries=5):
        for attempt in range(retries):
            try:
                async with session.get(url, headers={'User-Agent': self.user_agent}, timeout=20) as response:
                    print(f'{Fore.CYAN}Fetching {url} - Status: {response.status}{Style.RESET_ALL}')

                    if response.status == 200:
                        return response
                    elif response.status == 404:
                        print(f'{Fore.YELLOW}Page not found: {url}{Style.RESET_ALL}')
                        return None
                    elif response.status == 401:
                        print(f'{Fore.RED}Unauthorized access to {url}: Status {response.status}{Style.RESET_ALL}')
                        return None
                    elif response.status >= 500:
                        print(f'{Fore.RED}Server error at {url}: Status {response.status}. Retrying...{Style.RESET_ALL}')
                        await asyncio.sleep(2)
                        continue
                    else:
                        print(f'{Fore.YELLOW}Failed to fetch {url}: Status {response.status}{Style.RESET_ALL}')
                        return None

            except asyncio.TimeoutError:
                print(f'{Fore.RED}Timeout error fetching {url} on attempt {attempt + 1}{Style.RESET_ALL}')
                await asyncio.sleep(2)
            except Exception as e:
                print(f'{Fore.RED}Error fetching {url} on attempt {attempt + 1}: {e}{Style.RESET_ALL}')
                await asyncio.sleep(2)

        print(f'{Fore.RED}All attempts to fetch {url} failed.{Style.RESET_ALL}')
        return None

    async def check_wordpress(self, session):
        wordpress_files = [
            'wp-login.php',
            'wp-admin/',
            'wp-includes/',
            'wp-content/',
            'wp-json/wp/v2/'
        ]

        wordpress_reliable_files = [
            'readme.html',
            'wp-json/wp/v2/',
            'xmlrpc.php'
        ]

        print(f"{Fore.GREEN}\nChecking if site is a WordPress site...{Style.RESET_ALL}")
        
        for path in wordpress_files:
            url = f"{self.url}/{path}"
            response = await self.fetch(session, url)
            if response:
                print(f'{Fore.GREEN}WordPress detected via: {url}{Style.RESET_ALL}')
                break
        else:
            for reliable_path in wordpress_reliable_files:
                url = f"{self.url}/{reliable_path}"
                response = await self.fetch(session, url)
                if response:
                    print(f'{Fore.GREEN}WordPress detected via reliable method: {url}{Style.RESET_ALL}')
                    break
            else:
                print(f'{Fore.RED}Not a WordPress site.{Style.RESET_ALL}')
                return False

        response = await self.fetch(session, self.url)
        if response:
            try:
                main_content = await response.text()
                if '<meta name="generator" content="WordPress' in main_content:
                    print(f'{Fore.GREEN}WordPress detected via meta tag.{Style.RESET_ALL}')
                    return True
            except Exception as e:
                print(f'{Fore.RED}Error reading main page content: {e}{Style.RESET_ALL}')
        
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

        print(f"{Fore.GREEN}\nChecking for directory listings...{Style.RESET_ALL}")
        
        for directory, name in zip(directories, dir_names):
            response = await self.fetch(session, self.url + '/' + directory)
            if response and 'Index of' in response:
                self.files.add(directory)
                print(f'{Fore.GREEN}{name} directory has directory listing enabled at: {self.url + "/" + directory}{Style.RESET_ALL}')
            else:
                print(f'{Fore.YELLOW}{name} directory does not have directory listing enabled at: {self.url + "/" + directory}{Style.RESET_ALL}')


    async def is_xml_rpc(self, session):
        print(f"{Fore.GREEN}\nChecking XML-RPC on {self.url}...{Style.RESET_ALL}")
        url = f'{self.url}/xmlrpc.php'
        response = await self.fetch(session, url)
        
        if response is not None:
            print(f'{Fore.GREEN}XML-RPC Interface available under: {url}{Style.RESET_ALL}')
        else:
            print(f'{Fore.RED}Failed to fetch XML-RPC interface at: {url}{Style.RESET_ALL}')

        try:
            async with session.get(url, headers={'User-Agent': self.user_agent}) as resp:
                if resp.status == 200:
                    print(f'{Fore.GREEN}XML-RPC Interface accessible at: {url}{Style.RESET_ALL}')
                elif resp.status == 404:
                    print(f'{Fore.RED}XML-RPC interface is not available (404 error).{Style.RESET_ALL}')
                else:
                    print(f'{Fore.YELLOW}XML-RPC interface inaccessible (Status: {resp.status}).{Style.RESET_ALL}')
        except Exception as e:
            print(f'{Fore.RED}Error checking XML-RPC status: {e}{Style.RESET_ALL}')

    async def check_robots_text(self, session):
        print(f"{Fore.GREEN}\nChecking robots.txt on {self.url}...{Style.RESET_ALL}")
        response = await self.fetch(session, f'{self.url}/robots.txt')
        
        if response:
            print(f'{Fore.GREEN}robots.txt available under: {self.url}/robots.txt{Style.RESET_ALL}')
            lines = response.split('\n')
            for l in lines:
                if 'Disallow:' in l:
                    print(f'{Fore.YELLOW}Interesting entry from robots.txt: {l}{Style.RESET_ALL}')
        else:
            print(f'{Fore.RED}Failed to fetch robots.txt.{Style.RESET_ALL}')

    async def check_full_path_disclosure(self, session):
        print(f"{Fore.GREEN}\nChecking for Full Path Disclosure on {self.url}...{Style.RESET_ALL}")
        response = await self.fetch(session, self.url + '/wp-includes/rss-functions.php')
        
        if response:
            regex = re.compile('Fatal error:.*? in (.*?) on', re.S)
            matches = regex.findall(response)

            if matches:
                exposed_path = matches[0].replace('\n', '').strip()
                print(f'{Fore.RED}Full Path Disclosure (FPD) detected in: {self.url + "/wp-includes/rss-functions.php"}{Style.RESET_ALL}')
                print(f'{Fore.RED}Exposed Path: {exposed_path}{Style.RESET_ALL}')
            else:
                print(f'{Fore.YELLOW}No Full Path Disclosure detected.{Style.RESET_ALL}')
        else:
            print(f'{Fore.RED}Failed to fetch rss-functions.php for FPD check.{Style.RESET_ALL}')

    async def enum_wordpress_users(self, session):
        print(f'{Fore.GREEN}\nEnumerating WordPress users on {self.url}...{Style.RESET_ALL}')
        url = f'{self.url}/wp-json/wp/v2/users?page=1&per_page=100'
        response = await self.fetch(session, url)

        if response and response.status == 200:
            current_users = await response.json()
            print(f'Fetched users: {len(current_users)} found.')
            for user in current_users:
                print(f'{Fore.GREEN}Identified user: ID: {user["id"]}, Name: {user["name"]}, Slug: {user["slug"]}{Style.RESET_ALL}')
        else:
            print(f'{Fore.RED}Failed to fetch user data.{Style.RESET_ALL}')

    # Recode (Better way of enum_wordpress_users (in the works))
    """async def enum_wordpress_users(self, session):
        print(f'{Fore.GREEN}\nEnumerating WordPress users on {self.url}...{Style.RESET_ALL}')
        users = []
        page = 1
        per_page = 5

        while True:
            url = f'{self.url}/wp-json/wp/v2/users?page={page}&per_page={per_page}'
            response = await self.fetch(session, url)

            if response:
                if 'X-WP-Total' in response.headers:
                    total_users = response.headers['X-WP-Total']
                    print(f'Total users available: {total_users}')

                try:
                    text = await response.text()
                    user_pattern = re.compile(r'"id":\s*(\d+),"name":\s*"([^"]+)","slug":\s*"([^"]+)","email":\s*"([^"]*)"')
                    current_users = user_pattern.findall(text)

                    if current_users:
                        print(f'Fetched page {page}: {len(current_users)} users found.')
                        for user in current_users:
                            user_id, user_name, user_slug, user_email = user
                            print(f'{Fore.GREEN}Identified user: ID: {user_id}, Name: {user_name}, Slug: {user_slug}, Email: {user_email}{Style.RESET_ALL}')
                        
                        users.extend(current_users)
                        page += 1
                    else:
                        print(f'{Fore.YELLOW}No more users found on page {page}.{Style.RESET_ALL}')
                        break

                except Exception as e:
                    print(f'{Fore.RED}Unexpected error: {e}{Style.RESET_ALL}')
                    break
            else:
                print(f'{Fore.RED}Failed to fetch user data.{Style.RESET_ALL}')
                break

        self.users = users
        if not users:
            print(f'{Fore.YELLOW}No users found.{Style.RESET_ALL}')"""

    async def extract_version(self, response):
        print(f"{Fore.GREEN}Extracting WordPress version...{Style.RESET_ALL}")
        match = re.search(r'Version ([0-9]+\.[0-9]+\.?[0-9]*)', response)
        
        if match:
            version = match.group(1)
            print(f'{Fore.GREEN}WordPress version found: {version}{Style.RESET_ALL}')
            return version
        
        print(f'{Fore.RED}WordPress version not found in the response.{Style.RESET_ALL}')
        return None

    async def crawl_sitemap_for_forms(self, session, processed_urls=None):
        if processed_urls is None:
            processed_urls = set()

        robots_url = f"{self.url}/robots.txt"
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
                                        print(f'{Fore.GREEN}Form detected at: {sitemap_url}{Style.RESET_ALL}')
                                        break  

                    for sitemap_url in urls:
                        if sitemap_url.endswith('.xml'):
                            nested_forms = await self.crawl_sitemap_for_forms(session, processed_urls)
                            forms_with_input.extend(nested_forms)

                    return forms_with_input
                else:
                    print(f'{Fore.RED}Failed to fetch sitemap URL: {sitemap_url}{Style.RESET_ALL}')
            else:
                print(f'{Fore.YELLOW}Sitemap URL {sitemap_url} has already been processed or is not found.{Style.RESET_ALL}')
        else:
            print(f'{Fore.RED}Failed to fetch robots.txt from: {robots_url}{Style.RESET_ALL}')

        return []

    async def check_themes(self, session):
        print(f'{Fore.GREEN}\nChecking installed themes on {self.url}...{Style.RESET_ALL}')
    
    async def check_plugins(self, session):
        print(f'{Fore.GREEN}\nChecking installed plugins on {self.url}...{Style.RESET_ALL}')
        plugin_directory_url = f'{self.url}/wp-content/plugins/'
        rest_api_plugins_url = f'{self.url}/wp-json/plugins/v1/all'
        known_plugins = [
            'wordpress-seo/wp-seo.php',                  # Yoast SEO
            'akismet/akismet.php',                        # Akismet
            'woocommerce/woocommerce.php',                # WooCommerce
            'elementor/elementor.php',                    # Elementor Page Builder
            'wpforms-lite/wpforms.php',                   # WPForms
            'contact-form-7/wp-contact-form-7.php',      # Contact Form 7
            'jetpack/jetpack.php',                        # Jetpack
            'wp-super-cache/wp-cache.php',                # WP Super Cache
            'wp-rocket/wp-rocket.php',                    # WP Rocket
            'gravityforms/gravityforms.php',             # Gravity Forms
            'bbpress/bbpress.php',                        # bbPress
            'wpml-multilingual-cms/wpml.php',            # WPML
            'nextgen-gallery/nggallery.php',              # NextGEN Gallery
            'wordfence/wordfence.php',                    # Wordfence Security
            'duplicate-post/duplicate-post.php',          # Duplicate Post
            'updraftplus/updraftplus.php',                # UpdraftPlus
            'redirection/redirection.php',                # Redirection
            'all-in-one-seo-pack/all_in_one_seo_pack.php',  # All in One SEO Pack
            'mailchimp-for-wp/mailchimp-for-wp.php',     # Mailchimp for WordPress
            'social-warfare/social-warfare.php',          # Social Warfare
            'wp-optimize/wp-optimize.php',                # WP-Optimize
            'monsterinsights/google-analytics-for-wordpress.php',  # MonsterInsights
            'schema-and-structured-data-for-wp/schema-and-structured-data-for-wp.php',  # Schema & Structured Data for WP
            'wp-job-manager/wp-job-manager.php',          # WP Job Manager
            'wp-user-frontend/wp-user-frontend.php',      # WP User Frontend
            'redirection/redirection.php',                # Redirection
            'smush/wp-smush.php',                         # Smush Image Compression
            'duplicator/duplicator.php',                  # Duplicator
            'wp-cli/faq',                                # WP-CLI
            'livechat/livechat.php',                      # LiveChat
            'tablepress/tablepress.php',                  # TablePress
            'contact-form-7/wp-contact-form-7.php',      # Contact Form 7
            'wp-smtp/wp-smtp.php',                        # WP Mail SMTP
            'wp-customer-reviews/wp-customer-reviews.php', # WP Customer Reviews
            'login-lockdown/login-lockdown.php',          # Login LockDown
            'insert-headers-and-footers/insert-headers-and-footers.php', # Insert Headers and Footers
            'schema-woocommerce/schema-woocommerce.php',  # Schema & Structured Data for WooCommerce
            'wp-maintenance-mode/wp-maintenance-mode.php', # WP Maintenance Mode
            'shortcodes-ultimate/shortcodes-ultimate.php', # Shortcodes Ultimate
            'google-site-kit/google-site-kit.php',        # Site Kit by Google
            'elementor-pro/elementor.php',                # Elementor Pro
            'memberpress/memberpress.php',                # MemberPress
            'wp-ultimate-recipe/wp-ultimate-recipe.php', # WP Ultimate Recipe
            'popup-maker/popup-maker.php',                # Popup Maker
            'advanced-custom-fields/acf.php',            # Advanced Custom Fields
            'nextgen-gallery/nggallery.php',              # NextGEN Gallery
            'wp-testimonial/wordpress-testimonial.php',  # WP Testimonials
        ]

        response = await self.fetch(session, plugin_directory_url)
        if response and 'Index of' in response:
            print(f'{Fore.GREEN}Plugin directory listing found at: {plugin_directory_url}{Style.RESET_ALL}')

        response = await self.fetch(session, rest_api_plugins_url)
        if response:
            try:
                plugins = json.loads(response)
                print(f'{Fore.GREEN}Installed Plugins from REST API:{Style.RESET_ALL}')
                for plugin in plugins:
                    print(f'{Fore.GREEN}{plugin["name"]} - Version: {plugin["version"]}{Style.RESET_ALL}')
            except json.JSONDecodeError:
                print(f'{Fore.RED}Failed to decode JSON response from the REST API.{Style.RESET_ALL}')

        for plugin in known_plugins:
            plugin_url = f'{self.url}/wp-content/plugins/{plugin}'
            response = await self.fetch(session, plugin_url)
            if response:
                print(f'{Fore.GREEN}Known plugin found: {plugin}{Style.RESET_ALL}')

    async def check_themes(self, session):
        print(f'{Fore.GREEN}\nChecking installed themes on {self.url}...{Style.RESET_ALL}')
        
        theme_directory_url = f'{self.url}/wp-content/themes/'
        rest_api_themes_url = f'{self.url}/wp-json/wp/v2/themes'
        known_themes = [
            'twentytwentyone',           # Twenty Twenty-One
            'twentytwentytwo',           # Twenty Twenty-Two
            'astra',                     # Astra
            'divi',                      # Divi
            'generatepress',             # GeneratePress
            'oceanwp',                   # OceanWP
            'hello-elementor',           # Hello Elementor (Elementor)
            'neve',                      # Neve
            'flatsome',                  # Flatsome
            'hestia',                    # Hestia
            'avada',                     # Avada
            'beaver-builder',            # Beaver Builder
            'soledad',                   # Soledad
            'wp-bootstrap-blocks',       # WP Bootstrap Blocks
            'storefront',                # Storefront (WooCommerce)
            'sydney',                    # Sydney
            'kalium',                    # Kalium
            'salient',                   # Salient
            'ultra',                     # Ultra
            'enfold',                    # Enfold
            'blocksy',                   # Blocksy
            'total',                     # Total
            'porto',                     # Porto
            'neve',                      # Neve
            'phlox',                     # Phlox
            'jevelin',                   # Jevelin
            'zakra',                     # Zakra
            'archi',                     # Archi
            'bridge',                    # Bridge
            'generateblocks',            # GenerateBlocks
            'wp-ninja',                  # WP Ninja
            'shapely',                   # Shapely
            'genesis',                   # Genesis Framework
            'divi-builder',              # Divi Builder
            'mystique',                  # Mystique
            'dixie',                     # Dixie
            'kALLYAS',                   # KALLYAS
            'newspaper',                 # Newspaper
            'customify',                 # Customify
            'uncode',                    # Uncode
            'salient',                   # Salient
            'fastest',                   # Fastest
            'semplice',                  # Semplice
            'kalium',                    # Kalium
            'x',                         # X Theme
            'beach',                     # Beach
            'florence',                  # Florence
            'patreon',                   # Patreon
            'bento',                     # Bento
            'woodmart',                  # WoodMart
            'shopkeeper',                # Shopkeeper
            'oulex',                     # Oulex
            'consulting',                # Consulting
            'magazine',                  # Magazine
        ]

        response = await self.fetch(session, theme_directory_url)
        if response and 'Index of' in response:
            print(f'{Fore.GREEN}Theme directory listing found at: {theme_directory_url}{Style.RESET_ALL}')

        response = await self.fetch(session, rest_api_themes_url)
        if response:
            try:
                themes = json.loads(response)
                print(f'{Fore.GREEN}Installed Themes from REST API:{Style.RESET_ALL}')
                for theme in themes:
                    print(f'{Fore.GREEN}{theme["name"]} - Version: {theme["version"]}{Style.RESET_ALL}')
            except json.JSONDecodeError:
                print(f'{Fore.RED}Failed to decode JSON response from the REST API.{Style.RESET_ALL}')

        for theme in known_themes:
            theme_url = f'{self.url}/wp-content/themes/{theme}'
            response = await self.fetch(session, theme_url)
            if response:
                print(f'{Fore.GREEN}Known theme found: {theme}{Style.RESET_ALL}')

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
                'check-themes': self.check_themes,
            }

            for check in checks:
                if check in check_methods:
                    tasks.append(check_methods[check](session))

            await asyncio.gather(*tasks)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='WordPress Scanner')
    parser.add_argument('url', help='The URL of the WordPress site to scan')
    parser.add_argument('--user-agent', default='Wordpresscan - For educational purpose only!', help='User agent to use')
    parser.add_argument('--checks', default='wordpress', help='Comma-separated list of checks to perform: wordpress, readme, debug-log, backup-file, directory-listing, xml-rpc, robots-text, full-path-disclosure, enum-users, sitemap-forms, check-plugins, check-themes')

    args = parser.parse_args()
    checks = args.checks.split(',')

    scanner = AsyncWordPressScanner(args.url, args.user_agent)
    asyncio.run(scanner.scan(checks))
