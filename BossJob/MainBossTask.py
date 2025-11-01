import json
import random
from Utils.Config import Config
from Utils.AiAsk import AiAsk
from curl_cffi import requests
from BossJob.ZhiPinEnum import ZhiPinUrl
import time
from BossJob.BossTab import BossTab
import logging
from Utils.Utils import format_map, ask_result_to_bool, get_local_json
import os
import atexit

log = logging.getLogger(__name__)
config = Config('boss')
ai_config = Config('ai')

old_jobs_path = '../tmp/BossJobList.json'
boss_answer_path = '../tmp/BossAnswerList.json'

headers = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0",
  "Connection": "keep-alive",
  "Accept": "application/json, text/plain, */*",
  "Accept-Encoding": "gzip, deflate, br, zstd",
  "sec-ch-ua-platform": "\"Windows\"",
  "sec-ch-ua": "\"Microsoft Edge\";v=\"141\", \"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"141\"",
  "sec-ch-ua-mobile": "?0",
  "x-requested-with": "XMLHttpRequest",
  "sec-fetch-site": "same-origin",
  "sec-fetch-mode": "cors",
  "sec-fetch-dest": "empty",
  "referer": "https://www.zhipin.com/web/geek/jobs",
  "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,zh-TW;q=0.5",
  "priority": "u=1, i"
}
job_urls = [ZhiPinUrl.JobList.format_url(city=city,job_type=config['job_type'],salary=config['salary'],
                                         experience=config['experience'],degree=','.join(map(str,config['degree'])),
                                         industry=','.join(map(str,config['industry'])),
                                         scale=','.join(map(str,config['scale']))) for city in config['city_list']]
def get_expect_list(cookies):
    res = requests.get(ZhiPinUrl.ExpectList.value.format(time=int(time.time()*1000)),impersonate='chrome110',headers= headers,
                       cookies=cookies)
    if res.status_code == 200:
        data = res.json()
        t = []
        for e_item in data['zpData']['expectList']:
            t.append({'encryptId': e_item['encryptId'], 'jobName': e_item['positionName']})
        return t
    return None

def get_job_detail(s_id,lid, b: BossTab):
    res = requests.get(ZhiPinUrl.JobDetail.format_url(securityId=s_id,lid=lid,time=int(time.time()*1000)),
                       impersonate='chrome110',headers= headers,cookies=b.get_cookies_to_dict())
    if res.status_code == 200:
        data = res.json()
        # log.info(data)
        return data
    return None

def add_boss(url,cookie):
    res = requests.get(url,impersonate='chrome110',headers= headers,cookies=cookie)
    if res.status_code == 200:
        try:
            if res.json().get('message',None) == 'Success':
                return True
        except Exception as e:
            log.warning(e)
            return False
    return False

def get_job_list(encrypt_id, b: BossTab, old_job_ids):
    all_jobs = []
    max_num = 20
    def get_json_single_url(url, page_num=1, accumulated_jobs=None):
        """获取单个URL的分页数据"""
        if accumulated_jobs is None:
            accumulated_jobs = []
        try:
            url_1 = url.format(encryptExpectId=encrypt_id, time=int(time.time() * 1000), page_num=page_num)
            # log.info(url)
            res = requests.get(
                url_1,
                impersonate='chrome110',
                headers=headers,
                cookies=b.get_cookies_to_dict()
            )
            if res.status_code == 200:
                data = res.json()

                # 安全获取数据
                zp_data = data.get('zpData', {})
                current_jobs = zp_data.get('jobList', [])
                has_more = zp_data.get('hasMore', False)
                log.info(f"获取第{page_num}页数据，大小为{len(current_jobs)}")
                # 累积当前页面的工作数据
                filtered_jobs = [job for job in current_jobs if job.get('encryptJobId') not in old_job_ids]
                accumulated_jobs.extend(filtered_jobs)
                log.info(f"当前累计工作数量: {len(accumulated_jobs)}")

                # 如果还有更多数据，继续递归获取
                if has_more and page_num < max_num:  # 防止无限递归
                    time.sleep(random.randint(10,15))
                    return get_json_single_url(url, page_num + 1, accumulated_jobs)
                else:
                    return accumulated_jobs
            else:
                log.warning(f"请求失败，状态码: {res.status_code}")
                return accumulated_jobs

        except Exception as e:
            log.warning(f"获取数据时发生错误: {e}")
            return accumulated_jobs

    # 遍历所有城市URL
    for index, j_item in enumerate(job_urls):
        log.info(f"正在处理第{index + 1}个城市...")
        # log.info(j_item)
        time.sleep(10)  # 城市间的延迟
        city_jobs = get_json_single_url(j_item)
        all_jobs.extend(city_jobs)
        log.info(f"城市{index + 1}完成，获取到{len(city_jobs)}个工作")

    return all_jobs

def main():
    log.info("正在初始化配置")
    log.info("正在导入本地记录的已经查询过的职业和回答过的boss")
    os.makedirs('../tmp', exist_ok=True)
    old_jobs = get_local_json(old_jobs_path,[])
    boss_answer = get_local_json(boss_answer_path, [])
    def onclose():
        with open(old_jobs_path, 'w', encoding='utf-8') as f:
            json.dump(old_jobs, f, ensure_ascii=False, indent=4)
        with open(boss_answer_path, 'w', encoding='utf-8') as f:
            json.dump(boss_answer, f, ensure_ascii=False, indent=4)
    atexit.register(onclose)
    log.info("正在执行Boss直聘任务")
    log.info("正在初始化浏览器")
    b = BossTab()
    log.info("初始化完成")
    log.info("正在初始化ai模型")
    ai = AiAsk(ai_config['api_key'], ai_config['model'],ai_config['base_url'])
    if not ai.test_client():
        log.warning("ai模型连接测试失败，请检查相关配置以及报错")
        log.warning("程序已经关闭，请检查错误日志")
        return
    e_l = get_expect_list(b.get_cookies_to_dict())
    log.info(f"获取到{len(e_l)}个意向职位")
    for item in e_l:
        log.info(f"当前正在查找的期望工作为{item['jobName']}")
        all_job_list = get_job_list(item['encryptId'], b, old_jobs)
        log.info(json.dumps(all_job_list,ensure_ascii= False))
        for index, job in enumerate(all_job_list):
            log.warning("="*30)
            log.info(f"正在处理第{index + 1}个职位")
            log.info(f"剩余工作数量为{len(all_job_list) - index}个")
            log.info(f"正在获取岗位-{job['jobName']}-详情")
            job_detail = get_job_detail(job['securityId'], job['lid'], b)
            v1 = job_detail.get("zpData").get("jobInfo")
            v1.update(job_detail.get("zpData").get("bossInfo"))
            v1["showSkills"] = str(v1.get("showSkills",""))
            v1["resume"] = ai_config['resume']
            v1['job_info'] = format_map(ai_config['job_info'], v1)
            old_jobs.append(job['encryptJobId'])
            log.info(f"当前岗位的工作地点为: {v1['locationName']}")
            log.info(f"当前岗位的薪资为：{v1['salaryDesc']}")
            log.info(f"当前岗位的公司为：{v1['address']}")
            time.sleep(random.randint(5,10))
            if job_detail is None:
                log.warning(f"获取岗位{job['jobName']}详情失败")
                continue
            log.info(f"正在处理岗位{job['jobName']}")
            log.info("开始过滤该岗位招聘者是否符合条件")
            result = ai.ask(format_map(ai_config['compare_prompt'],v1), format_map(ai_config['compare_system_prompt'],v1))
            log.info(f"ai的返回结果为: {result}")
            if not ask_result_to_bool(result):
                log.info("该职位不符合要求")
                continue
            if job.get('encryptJobId', None) in boss_answer:
                log.warning("该boss已经添加过")
                continue
            boss_answer.append(job.get('encryptJobId', None))
            log.info("该职位符合要求正在添加boss好友")
            add_boss(ZhiPinUrl.AddBossFriend.format_url(securityId=job['securityId'],encryptJobId=job['encryptJobId'],
                                                           lid=job['lid'],time=int(time.time()*1000)),b.get_cookies_to_dict())
            b.send_to_boss(ZhiPinUrl.Chat.format_url(encryptBossId=v1['encryptUserId'],
                                                                  encryptJobId=v1['encryptId'],
                                                                  securityId=job_detail['zpData']['securityId'],
                                                                  lid=job_detail['zpData']['lid'],time=int(time.time()*1000)),
                           lambda: ai.ask(format_map(ai_config['specific_prompt'], v1), format_map(ai_config['specific_system_prompt'], v1)))
            time.sleep(random.randint(5,10))
        log.info(f"期望工作{item['jobName']}以及处理完成\n\n")
if __name__ == '__main__':
    main()
