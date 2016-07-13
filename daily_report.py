# -*- coding: utf-8 -*- 

import urllib
import sys
import base64
import requests
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

class TracReport(object):
    def get_report_content(self, reportUrl, loginUrl, logoutUrl):
        if loginUrl is None:
            response = requests.get(reportUrl, verify=False)
            return response.content

        # get auth information
        with open(".auth", "r") as f:
            user = f.readline()
            password = base64.b64decode(f.readline())

        # get token
        session = requests.session()
        session.get(loginUrl, verify=False)

        data = dict(__FORM_TOKEN=session.cookies['trac_form_token'],
                    referer=reportUrl,
                    user=user,
                    password=password)

        response = session.post(loginUrl, 
                              urllib.urlencode(data), 
                              headers={'Content-Type' : 'application/x-www-form-urlencoded'}, 
                              verify=False)

        session.get(logoutUrl, verify=False)

        return response.content

    def parse_atm_csv(self, content, column):
        import StringIO
        res = StringIO.StringIO(content)
        titleline = res.readline().split()
        column_index = [titleline.index(value) for value in column]
        
        result = {}
        for line in res:
            content = line.replace("\r\n", '').split('\t')

            people = content[0]
            data = [content[index] for index in column_index] 

            # for idx, d in enumerate(data[:3]):
                # data[idx] = '<a href="">' + d + '</a>' 

            # if data != []:
            result.setdefault(people, []).append(data)
        return result

    def get_task_report(self, reportUrl):
        content = self.get_report_content(reportUrl, None, None)
        column = ['ticket', 'summary', 'milestone', 'status', 'Modified']
        result = self.parse_atm_csv(content, column)
        return result

    def get_bug_report(self, reportUrl):
        loginUrl = 'https://trac.genienrm.com/TICKET/login'
        logoutUrl = 'https://trac.genienrm.com/TICKET/logout'

        content = self.get_report_content(reportUrl, loginUrl, logoutUrl)
        column = ['ticket', 'summary', 'priority', 'status', 'Modified']
        result = self.parse_atm_csv(content, column)
        return result

def merge_ticket_atm_data(task, bug):
    report = {}
    for people, data_list in task.iteritems():
        report.setdefault(people, {})['task'] = data_list
    for people, data_list in bug.iteritems():
        report.setdefault(people, {})['bug']= data_list

    return report

def print_report(report):
    for key in sorted(report.keys()):
        print key
        for key_type, data_list in report[key].iteritems():
            print '\t' + key_type
            for data in data_list:
                print '\t\t',
                for d in data:
                    print d,
                print 

class GenHtmlTable(object):
    def gen_people_tbody(self, people, count):

        return '''<tbody>
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

    def gen_data_title(self, data_type):
        title_column = ['ticket', 'summary', 'milestone', 'status', 'Modified'] if data_type == 'task' else ['ticket', 'summary', 'priority', 'status', 'Modified']
        return '''\t\t<tr class="trac-columns">
            <th><a href="">%s</a></th>
        </tr>\n''' % '</a></th><th><a href="">'.join(title_column)

    def fill_hyperlink(self, data_type, data):
        ticket_num = data[0]
        data[0] = '#' + ticket_num

        if data_type == 'task':
            link_url = 'https://trac.genienrm.com/ATM6/ticket/%s' % ticket_num
        elif data_type == 'bug':
            link_url = 'https://trac.genienrm.com/TICKET/ticket/%s' % ticket_num

        for idx, d in enumerate(data[:3]):
            data[idx] = '<a href="{0}">{1}</a>'.format(link_url, d)

        return data

    def fill_tr_style(self, index, data_type, data):

        class_even = "even" if (index % 2) == 0 else "odd"
        background_color = ''
        if data_type == 'task':
            column = data[3]
            style_map = ['Spec', 'Design', 'Job', 'new']
        elif data_type == 'bug':
            column, status = data[2:4]
            style_map = ['立即解決', '立即查找', '安排時程', '留待察看']

            if  status == 'reviewing':
                background_color = 'style="background-color: #C7EDCC;"'
            elif status == 'resovled' or status == 'closed':
                background_color = 'style="background-color: #CCCCCC; font-style: italic;"'
        try:
            style_index = style_map.index(column) + 1
        except ValueError:
            style_index = 3

        return 'class="color{0}-{1}" {2}'.format(style_index, class_even, background_color)

    def gen_data_tr(self, index, data_type, data):
        style = self.fill_tr_style(index, data_type, data)
        data = self.fill_hyperlink(data_type, data)
        content = '\t\t\t<td>' + '</td>\n\t\t\t<td>'.join(data) + '</td>\n'
        return '\t\t<tr %s>\n%s\t\t</tr>\n' % (style, content)

    def gen_ticket_tbody(self, data_type, data_list):
        data_tr =  self.gen_data_title(data_type)
        for idx, data in enumerate(data_list):
            data_tr += self.gen_data_tr(idx, data_type, data)

        return '\t<tbody>\n%s\t</tbody>\n' % data_tr
        
    def gen_html_table(self, report):

        table_html = ''
        for people in sorted(report.keys()):
            table_html += self.gen_people_tbody(people, len(report[people]['task']) + len(report[people]['bug']))
            for data_type, data_list in report[people].iteritems():
                table_html += self.gen_ticket_tbody(data_type, data_list)

        html = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
        <link rel="stylesheet" href="css/trac.css" type="text/css" />
        <link rel="stylesheet" href="css/report.css" type="text/css" />
        <link rel="tracwysiwyg.stylesheet" href="css/trac.css" />
    </head>
    <body>
        <table class="listing tickets">
%s
        </table>
    </body>
</html>
        ''' % table_html

        print html

def main():
    if sys.argv[1] == 'pd1':
        taskUrl = 'https://trac.genienrm.com/ATM6/report/28?asc=1&format=tab'
        bugUrl = 'https://trac.genienrm.com/TICKET/report/40?asc=1&format=tab'
    elif sys.argv[1] == 'pd2':
        taskUrl = 'https://trac.genienrm.com/ATM6/report/29?asc=1&format=tab'
        bugUrl = 'https://trac.genienrm.com/TICKET/report/41?asc=1&format=tab'

    trac_report = TracReport()
    task_report = trac_report.get_task_report(taskUrl)
    bug_report = trac_report.get_bug_report(bugUrl)
    result = merge_ticket_atm_data(task_report, bug_report)
    #print_report(result)

    gen_html = GenHtmlTable()
    gen_html.gen_html_table(result)


if __name__ == '__main__':
    main()