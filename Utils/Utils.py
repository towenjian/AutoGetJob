import re
from DrissionPage import Chromium
import atexit

class BowserTab:
    bowser = Chromium()
    atexit.register(lambda : BowserTab.bowser.quit())



def ask_result_to_bool(res):
    """
    检查ai产生的字符串是否是True或者False
    :param res:
    :return: bool
    """
    clean_res = re.sub(r'[`*]', '', res).strip().lower()
    p = ['true', '是', 'ok', 'okay', 'y', 'yes']
    return any(k in clean_res for k in p)

def format_map(s,d):
    class SafeDict(dict):
        def __missing__(self, key):
            return '{' + key + '}'

    safe_dict = SafeDict(d)
    s = s.format_map(safe_dict)
    return s

def get_local_json(path, default_value=None):
    """
    通用的本地JSON文件读取函数
    :param path: JSON文件路径
    :param default_value: 文件不存在时的默认值
    :return: JSON数据或默认值
    """
    import os
    import json
    if not os.path.exists(path):
        # 创建目录（如果不存在）
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # 保存默认值到文件
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(default_value, f, ensure_ascii=False, indent=4)
        return default_value

    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"读取JSON文件失败: {e}")
        return default_value