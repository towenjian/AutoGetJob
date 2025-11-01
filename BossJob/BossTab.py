from collections.abc import Callable
from DrissionPage._units.listener import DataPacket
import logging
from Utils.Utils import BowserTab
log = logging.getLogger(__name__)
Boss_Url = 'https://www.zhipin.com/web/user/?ka=header-login'

class BossTab(BowserTab):

    def __init__(self):
        # 提前启动聊天页面
        self.chat= self.bowser.new_tab()
        self.chat.listen.start("geek/historyMsg")
        self.chat.listen.pause(True)
        # 主页面
        self.tab = self.bowser.new_tab()
        self.tab.get(Boss_Url)
        self.tab.wait(5)
        self.wait_bypass(30)
        is_login, t2 = self.is_login()
        if is_login:
            t2.click()
            self.tab.wait(5)
            self.wait_bypass(30)
            try:
                self.tab.wait.url_change('https://www.zhipin.com/')
                log.info('登录成功')
            except Exception:
                log.warning("登录时间过长或已经登录成功，请重新启动")
                exit(1)
        to_job = self.tab.ele('@ka=header-jobs',timeout=3)
        self.tab.listen.start("/recommend/job/list.json")
        to_job.click()
        self.tab.listen.pause(True)
        self.tab.wait(5)



    def is_bypass(self):
        """
        没过码返回True
        :return: True and ele
        """
        t = self.tab.ele('当前 IP 地址可能存在异常访问行为，完成验证后即可正常使用.')
        return bool(t), t

    def wait_bypass(self,timeout=60):
        b, t = self.is_bypass()
        try:
            if b:
                log.info("正在等待过码")
                t.wait.deleted(timeout= timeout)
        except Exception:
            log.warning('验证时间过长已经退出程序')
            exit(1)

    def is_login(self):
        """
        没过码返回True
        :return: True and ele
        """
        t = self.tab.ele('@ka=header-login', timeout=3)
        return bool(t), t

    def get_cookies_to_dict(self):
        self.tab.listen.resume()
        to_job = self.tab.ele('@ka=header-jobs', timeout=3)
        to_job.click()
        self.wait_bypass(timeout=60*30)
        l = self.tab.listen.wait(timeout=5,count=1)
        if l is None:
            return None
        if isinstance(l, list):
            l1: DataPacket = l[-1]
            cookies_list = l1.request.cookies
            self.tab.listen.pause(True)
            return {item['name']: item['value'] for item in cookies_list}
        if isinstance(l, DataPacket):
            cookies_list = l.request.cookies
            self.tab.listen.pause(True)
            return {item['name']: item['value'] for item in cookies_list}
        cookies = self.tab.cookies()
        return {item['name']: item['value'] for item in cookies}

    def send_to_boss(self,url,get_ask:Callable):
        self.chat.listen.resume()
        self.chat.get(url)
        d = self.chat.listen.wait(timeout=5,count=1)
        if d is None:
            return
        if isinstance(d, list):
            d = d[-1]
        data = d.response.body
        if len(data['zpData']['messages'])>2:
            log.warning('当前Boss已经发送过消息了，已停止发送消息')
            return
        self.chat.listen.pause(True)
        self.chat.wait(5)
        input_k = self.chat.ele('@class=chat-input')
        input_k.click()
        msg = get_ask()
        if msg is None:
            log.warning('没有获取到消息，已退出程序')
            exit(1)
        log.info(f"正在发送消息: {msg}")
        input_k.input(msg)
        send_btn = self.chat.ele('@type=send')
        send_btn.click()



