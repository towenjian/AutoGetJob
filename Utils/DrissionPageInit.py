from DrissionPage import ChromiumOptions


path = r'你的浏览器运行路径，自行查找方法填入运行该文件即可'

ChromiumOptions().set_browser_path(path=path).save()