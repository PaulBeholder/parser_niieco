import csv

import config
import json
import requests
import time
from typing import Dict
from typing import List


def call_b24_method(method, params):
    ## работает
    """f = f"{config.B24_URL}crm.item.list.json?entityTypeId=140"
        method = "crm.deal.list"
        params =    {   "FILTER":  {
                                 "CATEGORY_ID":6
                        },
                        "SELECT":['ID','TITLE']
                    }
        q = call_b24_method(method,params)
    """
    if config.B24SLEEP:
        time.sleep(config.B24SLEEP)
    webhook = F'https://{config.B24_HOST}/rest/{config.B24_USER_ID}/{config.B24_WEBHOOK}/'
    endpoint = F'{webhook}{method}.json'

    ##endpoint = 'http://httpbin.org/get' ##для тестов


    params= _prepare_params(params)
    ##  if method == 'batch':
    ##      for i in params['cmd']:
    test = method.rsplit('.', -1)[2]
    if method.rsplit('.', -1)[2] in ['add', 'update', 'delete', 'set']:
        response = requests.post(endpoint, data=params)
    else:
        response = requests.get(endpoint, params)
    response = json.loads(response.text)
    if response['time']['operating'] >= 200:
        time.sleep(35)
    try:
        result_time = response['result']['result_time']
        result_time_last = result_time[response['result']['result_time'].__len__() - 1]
        result_time_last_operation = result_time_last['operating']
        if result_time_last_operation >= 200:
            time.sleep(35)
            print('Перегрев: ', result_time_last_operation)
    except:
        pass
    return response


def call_b24_batch(command):
    # Работает
    """Техническая функция"""
    batch = {'halt': '0'}
    batch['cmd'] = {}
    j = 0
    if isinstance(command,dict):
        for key, item in command.items():
            ii = _prepare_batch_params(item['params'])
            cm = f"{item['method']}%3F{ii}"  ## ?=%3F
            batch['cmd'][j] = cm
            j += 1
    else:
        for i in command:
            ii = _prepare_batch_params(i['params'])
            cm = f"{i['method']}%3F{ii}"  ## ?=%3F
            batch['cmd'][j] = cm
            j += 1
    result = call_b24_method("batch", batch)
    return result


def get_full_b24_list(method, params):
    # Работает
    """
    method = "crm.deal.list"
    params =    {   "FILTER":  {
                             "CATEGORY_ID":6
                    },
                    "SELECT":['ID','TITLE']
                }
    q = get_full_b24_list(method,params)
    print(q)"""
    start_time = time.time()
    result = call_b24_method(method, params)
    total = result['total']
    answer = result['result']
    if isinstance(answer, dict):
        answer = answer['items']
    command = []
    j = 0
    print(result['total'])
    for i in range(50, result['total'], 50):
        params_copy = params.copy()
        params_copy['start'] = i
        command.append({
            'method': method,
            'params': params_copy})
        j += 1
        if j == 50:
            res = call_b24_batch(command)
            res = res['result']['result']
            answer = write_res(answer, res, method)
            j = 0
            command = []
            process_time(start_time, total, i)
    if command:
        result = call_b24_batch(command)
        result = result['result']['result']
        answer = write_res(answer, result, method)
        process_time(start_time, total, len(command))
    return answer


def write_res(answer, res, method):
    if 'item' in method:
        for page in res:
            answer = answer + page['items']
    else:
        for page in res:
            answer = answer + page
    return answer


def unpack_b24_answer(answer, prev=''):
    # не работает
    ret = ''
    if isinstance(answer, dict):
        for key, value in answer.items():
            if (isinstance(value, list) or isinstance(value, tuple)) and len(value) > 0:
                for offset, val in enumerate(value):
                    if isinstance(val, dict):
                        unpack_b24_answer(answer['result'])


def call_b24_batch_full(fullCmd):
    # fullCmd = {'номер':'{method:str,params:dict}'}
    start_time = time.time()
    quantity_com = len(fullCmd)
    r_next = 0
    i = 0
    result = []
    if isinstance(fullCmd, dict):
        command = {}
        for key, item in fullCmd.items():
            if isinstance(item, tuple):
                (met, par) = item
                command[key] = dict(method = met['method'], params = par['params'])
            else:
                command[key] = item
            i += 1
            if i == 50:
                r = call_b24_batch(command)
                r_next += i
                process_time(start_time, quantity_com, key)
                r = r['result']['result']
                result.extend(r)
                command = []
                i = 0
        if i > 0:
            r = call_b24_batch(command)
            r_next += i
            process_time(start_time, quantity_com, len(command))
            r = r['result']['result']
            result.extend(r)
    else:
        command = []
        counter = 0
        for item in fullCmd:
            command.append(item)
            i += 1
            counter += 1
            if i == 50:
                r = call_b24_batch(command)
                r_next += i
                process_time(start_time, quantity_com, counter)
                r = r['result']['result']
                result.extend(r)
                command = []
                i = 0
        if i > 0:
            r = call_b24_batch(command)
            r_next += i
            process_time(start_time, quantity_com, counter)
            r = r['result']['result']
            result.extend(r)

    return result


def process_time(strat_time, quantity, quantity_step):
    time_step = time.time()
    delta = (time_step - strat_time)
    time_plan = delta * (quantity - quantity_step)/ quantity_step
    sec = time_plan % (24 * 3600)
    hour = sec // 3600
    sec %= 3600
    min_1 = sec // 60
    sec %= 60
    print(f"Осталось: %02d:%02d:%02d" % (hour, min_1, sec))
    print(f"{quantity_step}/{quantity}")
    return


def _prepare_params(params, prev=''):
    """Transforms list of params to a valid bitrix array."""
    ret = ''
    if isinstance(params, dict):
        for key, value in params.items():
            if isinstance(value, dict):
                if prev:
                    key = "{0}[{1}]".format(prev, key)
                ret += _prepare_params(value, key)
            elif (isinstance(value, list) or isinstance(value, tuple)) and len(value) > 0:
                for offset, val in enumerate(value):
                    if isinstance(val, dict):
                        ret += _prepare_params(
                            val, "{0}[{1}][{2}]".format(prev, key, offset))
                    else:
                        if prev:
                            ret += "{0}[{1}][{2}]={3}&".format(  ## &=%26
                                prev, key, offset, val)
                        else:
                            ret += "{0}[{1}]={2}&".format(key, offset, val)  ## &=%26
            else:
                if prev:
                    ret += "{0}[{1}]={2}&".format(prev, key, value)  ## &=%26
                else:
                    ret += "{0}={1}&".format(key, value)  ## &=%26
    return ret


def _prepare_batch_params(params, prev=''):
    """Transforms list of params to a valid bitrix array for Batch."""
    ret = ''
    if isinstance(params, dict):
        for key, value in params.items():
            if isinstance(value, dict):
                if prev:
                    key = "{0}[{1}]".format(prev, key)
                ret += _prepare_batch_params(value, key)
            elif (isinstance(value, list) or isinstance(value, tuple)) and len(value) > 0:
                for offset, val in enumerate(value):
                    if isinstance(val, dict):
                        ret += _prepare_batch_params(
                            val, "{0}[{1}][{2}]".format(prev, key, offset))
                    else:
                        if prev:
                            ret += "{0}[{1}][{2}]={3}%26".format(  ## &=%26
                                prev, key, offset, val)
                        else:
                            ret += "{0}[{1}]={2}%26".format(key, offset, val)  ## &=%26
            else:
                if prev:
                    ret += "{0}[{1}]={2}%26".format(prev, key, value)  ## &=%26
                else:
                    ret += "{0}={1}%26".format(key, value)  ## &=%26
    return ret


"""
method = "crm.deal.get"
with open('D:\Downloads\id_for_del.csv', 'r', encoding='utf-8') as csv_file:
    csv_w_file = csv.reader(csv_file, delimiter=',')
    command = []
    j = 0
    id_dic = list(csv_w_file)[0]
    print(len(id_dic))
    for i in id_dic:
        params = {  "ID": i,
                    "SELECT": ['ID', 'TITLE']
                 }
        command.append({
            'method': method,
            'params': params
        })

q = call_b24_batch_full(command)
print(q)
"""
