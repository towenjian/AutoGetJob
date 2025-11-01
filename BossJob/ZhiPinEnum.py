from enum import Enum
from string import Formatter


class ZhiPinUrl(Enum):
    # 岗位列表
    # JobList = 'https://www.zhipin.com/wapi/zpgeek/pc/recommend/job/list.json?pageSize=15&city={city}&mixExpectType&expectInfo&jobType={job_type}&salary={salary}&experience={experience}&degree={degree}&industry={industry}&scale={scale}&page={page_num}&encryptExpectId={encryptExpectId}&_={time}'
    JobList = 'https://www.zhipin.com/wapi/zpgeek/pc/recommend/job/list.json?page={page_num}&pageSize=15&city={city}&encryptExpectId={encryptExpectId}&mixExpectType=&expectInfo=&jobType={job_type}&salary={salary}&experience={experience}&degree={degree}&industry={industry}&scale={scale}&_={time}'
    # 岗位数据详情
    JobDetail = 'https://www.zhipin.com/wapi/zpgeek/job/detail.json?securityId={securityId}&lid={lid}&_={time}'
    # 意向职业列表
    ExpectList = 'https://www.zhipin.com/wapi/zpgeek/pc/recommend/expect/list.json?_={time}'
    # 聊天跳转
    Chat = 'https://www.zhipin.com/web/geek/chat?id={encryptBossId}&jobId={encryptJobId}&securityId={securityId}&lid={lid}'
    # 添加boss好友
    AddBossFriend = 'https://www.zhipin.com/wapi/zpgeek/friend/add.json?securityId={securityId}&jobId={encryptJobId}&lid={lid}&_={time}'

    def format_url(self, **kwargs):
        def clear_v(v):
            if isinstance(v, int):
                if v == 0:
                    return ''
                return str(v)
            return v
        url_template = self.value
        p = [filed[1] for filed in Formatter().parse(url_template) if filed[1]]
        format_args = {k:clear_v(v) for k,v in kwargs.items() if k in p}
        class SafeDict(dict):
            def __missing__(self, key):
                return '{' + key + '}'
        return url_template.format_map(SafeDict(**format_args))


