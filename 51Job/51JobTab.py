from Utils.Utils import BowserTab

job51_url = 'https://we.51job.com/pc/search'

class JobTab(BowserTab):
    def __init__(self):
        self.tab = self.bowser.new_tab()
        self.tab.get(job51_url)
        self.tab.listen.start('job/search-pc')

    def get_cookie_dict(self):
        pass

    def send_to_boss(self):
        pass