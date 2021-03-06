# -*- coding: utf-8 -*- 
import urllib
import sys
import base64
from lxml import etree
import pickle
import requests
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
from multiprocessing import Process, Queue, Pool

def login(loginUrl):
    with open(".auth", "r") as f:
        user = f.readline()
        password = base64.b64decode(f.readline())

    # get token
    session = requests.session()
    session.get(loginUrl, verify=False)

    data = dict(__FORM_TOKEN=session.cookies['trac_form_token'],
                # referer=reportUrl,
                user=user,
                password=password)

    response = session.post(loginUrl, 
                          urllib.urlencode(data), 
                          headers={'Content-Type' : 'application/x-www-form-urlencoded'}, 
                          verify=False)

    with open('.cookies', 'w') as f:
        pickle.dump(requests.utils.dict_from_cookiejar(session.cookies), f)

    return session


def get_login_seesion(loginUrl):
    try:
        with open('.cookies', 'r') as f:
            cookies = requests.utils.cookiejar_from_dict(pickle.load(f))
            session = requests.session()
            session.cookies = cookies
            return session
    except IOError:
        print 'Login ' + loginUrl
        return login(loginUrl)


def get_report_content(reportUrl, loginUrl):
    print "Get Data From: " + reportUrl
    if loginUrl is None:
        response = requests.get(reportUrl, verify=False)
        return response.content

    session = get_login_seesion(loginUrl)
    response = session.get(reportUrl, verify=False)

    return response.content


def gen_html_template(title, table_html):
    html = '''\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <link rel="stylesheet" href="css/trac.css" type="text/css" />
    <link rel="stylesheet" href="css/report.css" type="text/css" />
    <link rel="tracwysiwyg.stylesheet" href="css/trac.css" />
    <title> %s </title>
</head>
<body>
    <h1 class="report-result">
    %s
    </h1>
    <table class="listing tickets">
%s
    </table>
</body>
</html>
    ''' % (title, title, table_html)

    return html


def gen_people_tbody(people, count):

    return '''\
    <tbody>
        <tr class="trac-group">
          <th colspan="100">
            <h2 class="report-result">
                %s
                <span class="numrows">
                (%d matches)
                </span>
            </h2>
          </th>
        </tr>
    </tbody>\n''' % (
        people,
        count
    )


def gen_report_html(report_map):
    people_list = ['yungyu.wang',
                   'daniel.yang',
                   'jiarung.yeh',
                   'carl.yang',
                   'longline.yang',
                   'andy.huang',
                   'leo.shih',
                   'tingyu.lu',
                   'chim.pan',
                   'hank.kao',
                   'sadik.hung',
                   'shine.jian',
                   '_captain']
    def people_key(item):
        try:
            return people_list.index(item[0])
        except ValueError:
            return len(people_list)

    html = ''
    for people, tbody_list in sorted(report_map.iteritems(), key=people_key):
        ticket_num = reduce(lambda x, y: x+y , map(lambda x: len(x[1]), tbody_list))
        html += gen_people_tbody(people, ticket_num)
        for tr, tbody in tbody_list:
            tbody.insert(0, tr)
            html += etree.tostring(tbody)

    return html


def merge_table(html_list):
    page_list = [etree.HTML(html).xpath(u'//table[@class="listing tickets"]')[0] for html in html_list]
    title_list = [page.xpath(u'//tr[@class="trac-columns"]')[0] for page in page_list]
    group_list = [page.xpath(u'//h2[@class="report-result"]') for page in page_list]

    report_map = {}
    for idx in xrange(len(page_list)):
        page = page_list[idx]
        group = group_list[idx]
        title = title_list[idx]
        group_idx = 0
        for index in xrange(1, len(page), 2):
            tbody = page[index]
            people = group[group_idx].text.strip()
            report_map.setdefault(people, []).append((title, tbody))
            group_idx += 1

    return report_map


def worker(reportItem):
    reportUrl, isLogin, tracName, tracUrl = reportItem
    login = tracUrl + 'login/' if isLogin else None
    result = get_report_content(reportUrl, login).replace(tracName, tracUrl)

    print "End: " + reportUrl
    return result


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == 'mbo':
            taskItem = ('https://trac.genienrm.com/ATM6/report/25?max=500', False, '/ATM6/', 'https://trac.genienrm.com/ATM6/')
            task2Item = ('https://trac.genienrm.com/ATM5/report/21', False, '/ATM5/', 'https://trac.genienrm.com/ATM5/')
            bugItem = ('https://trac.genienrm.com/TICKET/report/24?max=500', True, '/TICKET/', 'https://trac.genienrm.com/TICKET/')
        elif sys.argv[1] == 'weekly':
            taskItem = ('https://trac.genienrm.com/ATM6/report/29?max=200', False, '/ATM6/', 'https://trac.genienrm.com/ATM6/')
            task2Item = ('https://trac.genienrm.com/ATM5/report/23', False, '/ATM5/', 'https://trac.genienrm.com/ATM5/')
            bugItem = ('https://trac.genienrm.com/TICKET/report/42', True, '/TICKET/', 'https://trac.genienrm.com/TICKET/')
        reportItemList = [taskItem, task2Item, bugItem]
        html_filename = sys.argv[1]+'.html'
    else:
        taskItem1 = ('https://trac.genienrm.com/ATM6/report/28', False, '/ATM6/', 'https://trac.genienrm.com/ATM6/')
        taskItem2 = ('https://trac.genienrm.com/ATM5/report/22', False, '/ATM5/', 'https://trac.genienrm.com/ATM5/')
        bugItem = ('https://trac.genienrm.com/TICKET/report/40', True, '/TICKET/', 'https://trac.genienrm.com/TICKET/')
        reportItemList = [taskItem1, taskItem2, bugItem]
        html_filename = 'pd.html'



    pool = Pool(len(reportItemList))
    report_list = pool.map(worker, reportItemList)

    report_map = merge_table(report_list)
    table_html = gen_report_html(report_map)
    
    html = gen_html_template(sys.argv[1], table_html)

    with open(html_filename, 'w') as f:
        f.write(html)

if __name__ == '__main__':
    main()
