
import argparse
import select
from selenium.webdriver.common.by import By

from browser_automation import BrowserManager, Node
from utils import Utility
from googl import Setup as GoogleSetup, Auto as GoogleAuto

PROJECT_URL = "https://www.edgen.tech/app"

class Setup:
    def __init__(self, node: Node, profile) -> None:
        self.node = node
        self.profile = profile
        self.google_setup = GoogleSetup(node, profile)
        
    def _run(self):
        self.google_setup._run()
        self.node.new_tab(f'https://www.edgen.tech/aura/tranlammain', method="get")
        Utility.wait_time(10)

class Auto:
    def __init__(self, node: Node, profile: dict) -> None:
        self.driver = node._driver
        self.node = node
        self.profile_name = profile.get('profile_name')
        self.email = profile.get('email')
        self.pwd_email = profile.get('pwd_email')
        self.google_auto = GoogleAuto(node, profile)

    def confirm_login(self):
        confirmed = False
        
        self.node.find_and_click(By.XPATH, '//span[@class[contains(., "block")] and normalize-space(.)="Aura Leaderboard"]/..')
        selectors = [
            (By.CSS_SELECTOR, "login-modal"),
            (By.CSS_SELECTOR, '[data-method="GOOGLE"]')
        ]
        btn_gg = self.node.find_in_shadow(selectors=selectors)
        if btn_gg:
            self.node.click(btn_gg)
            try:
                current_window = self.driver.current_window_handle

                if self.node.switch_tab('https://accounts.google.com'):
                    url_google = self.node.get_url()
                    if url_google:
                        if 'auth' in url_google:
                            if self.node.find_and_click(By.CSS_SELECTOR, f'[data-email="{self.email}"]'):
                                confirmed = True
                        elif 'signin' in url_google:
                            self.node.log(f'Cần đăng nhập google trước')
                            self.node.close_tab()
                    else:
                        self.node.log(f'Khôgn thể lấy url google')
                
                if confirmed:
                    if self.node.switch_tab('https://accounts.google.com'):
                        btns = self.node.find_all(By.TAG_NAME, 'button')
                        if len(btns) == 2:
                            self.node.click(btns[1]) # click continue
                        else:
                            self.node.log(f'Không tìm thấy đúng số lượng 2 btn: "cancel" và "continue"')
                            confirmed = False
                    else:
                        self.node.log(f'Trang accounts.google.com đã đóng')
                self.driver.switch_to.window(current_window)
            except Exception as e:
                self.node.log(f'Bị lỗi khi confirm đăng nhập google: {e}')

            return confirmed

    def loaded(self):
        for i in range(1,3):
            if self.node.find(By.CSS_SELECTOR, '[id="container"]'):
                self.node.log(f'Trang đã load [id="container"]')
                return True
            if i < 2:
                self.node.log(f'Try load again')
                self.node.reload_tab()
        return False

    def is_login(self):
        if not self.loaded():
            return None

        btn_leaderboard = self.node.find(By.XPATH, '//span[@class[contains(., "block")] and normalize-space(.)="Aura Leaderboard"]/..')
        if btn_leaderboard:
            text_btn = self.node.get_text(By.XPATH, './div[last()]', btn_leaderboard)
            
            if not text_btn:
                self.node.log(f'Không tìm thấy text sau dòng chữ "Aura Leaderboard"')
            if 'Join now'.lower() in text_btn.lower():
                self.node.log(f'Cần đăng nhập')

                return False
            else:
                self.node.log(f'Đã đăng nhập. Điểm hiện tại: {text_btn}')
                return True
        else:
            self.node.log(f'Không tìm thấy "Aura Leaderboard" để xác nhận login')
        
        return None

    def login(self):
        check_login = self.is_login()
        if check_login == False:
            self.confirm_login()
            Utility.wait_time(10)
            return self.is_login()
        elif check_login == True:
            return check_login

    def check_in(self):
        self.node.find_and_click(By.XPATH, '//span[@class[contains(., "block")] and normalize-space(.)="Aura Leaderboard"]/..')
        if not self.node.find(By.XPATH, '//p[contains(.,"Check-in")]'):
            return
        btns = self.node.find_all(By.TAG_NAME, 'button')
        for btn in btns:
            if 'Check In'.lower() in btn.text.lower():
                self.node.click(btn)
                break
        return True

    def _run(self):
        if not self.google_auto._run():
            self.node.snapshot(f'Chưa đăng nhập google. Có thể login dự án thất bại', False)
        self.node.new_tab(f'{PROJECT_URL}', method="get")
        if not self.login():
            self.node.snapshot(f'Login thất bại')
        if not self.check_in():
            self.node.snapshot(f'Check-in thất bại')

        point = self.node.get_text(By.XPATH, '//span[@class[contains(., "block")] and normalize-space(.)="Aura Leaderboard"]/../div[last()]')
        self.node.snapshot(f'Check-in thành công. Point: {point}')
        input('Enter')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--auto', action='store_true', help="Chạy ở chế độ tự động")
    parser.add_argument('--headless', action='store_true', help="Chạy trình duyệt ẩn")
    parser.add_argument('--disable-gpu', action='store_true', help="Tắt GPU")
    args = parser.parse_args()

    profiles = Utility.read_data('profile_name', 'email', 'pwd_email')
    max_profiles = Utility.read_config('MAX_PROFLIES')
    max_profiles = max_profiles[0] if max_profiles else 4
    
    if not profiles:
        print("Không có dữ liệu để chạy")
        exit()

    browser_manager = BrowserManager(AutoHandlerClass=Auto, SetupHandlerClass=Setup)
    # browser_manager.config_extension('Meta-Wallet-*.crx','OKX-Wallet-*.crx')
    browser_manager.run_terminal(
        profiles=profiles,
        max_concurrent_profiles=max_profiles,
        auto=args.auto,
        headless=args.headless,
        disable_gpu=args.disable_gpu,
    )