# -*- coding: utf-8 -*-
import re
import openai
from tenacity import retry,stop_after_attempt,wait_fixed
from loguru import logger
import subprocess
class CodeAgent:
    def __init__(self,model_name,openai_apikey):
        self.model = model_name
        self.openai_key = openai_apikey
        self.max_debug_num = 5
        self.curr_debug_num = 0
        self.test_case = []

    def add_testcase(self,input,output):
        self.test_case.extend([input,output])
        return self.test_case

    def clean_testcase(self):
        self.test_case = []
    @retry(stop = stop_after_attempt(5),wait = wait_fixed(20))
    def get_response(self,message):
        openai.api_key = self.openai_key
        cmp = openai.ChatCompletion.create(
            model = self.model,
            messages = message,
            temperature = 0.3
        )
        content = str(cmp['choices'][0]['message']['content'])
        while content.startswith ('\n'):
            content = content[1:]
        logger.info(f'第{self.curr_debug_num + 1}次生成结果:{content}')
        return content

    def run_code(self,extracted_code,input):
        with open('extracted_code.py','w',encoding = 'utf-8') as f:
            f.write(extracted_code + '\n')
        try:
            with subprocess.Popen(['python','extracted_code.py'],stdin = subprocess.PIPE,stdout = subprocess.PIPE,stderr = subprocess.PIPE,text = True) as process:
                process.stdin.write(input)
                process.stdin.flush()
                output,errors = process.communicate()
                return {'output':output.strip(),'errors':errors}
        except subprocess.CalledProcessError as e:
            return {'errors': e}



    def extract_code(self,code_content):
        pattern = '```python(.*?)```'
        matches = re.findall(pattern,code_content,re.DOTALL)
        extracted_code = '\n'.join(matches)
        return extracted_code.strip()

    def run_testcase(self,extracted_code):
        success_list = []
        fail_list = []
        input_text = self.test_case[0]
        expected_output = self.test_case[1]
        running_res = self.run_code(extracted_code,input_text)
        if running_res['errors'] == '':
            output = running_res['output']
        else:
            output = running_res['errors']
        if output == expected_output:
            logger.info(f'testcase{self.curr_debug_num+1}passed.\ninput:{input_text}\noutput:{output}\nexpected_output:{expected_output}')
            success_list.extend([input_text,expected_output])
        else:
            logger.info(f'testcase{self.curr_debug_num+1}failed.\ninput:{input_text}\noutput:{output}\nexpected_output:{expected_output}')
            fail_list.extend([input_text,output,expected_output])
        return{
            'success_list':success_list,
            'fail_list':fail_list
        }





    def runpipling(self,question):
        base_info = [{'role':'assistant','content':'你是一位ACM金牌选手，下面你来做一道代码题，请你给出python代码的解决方案，要求只输出可执行的代码，不要给出任何额外内容'},
                     {'role':'user','content':question}]
        self.response = self.get_response(base_info)
        self.extracted_code = self.extract_code(self.response)
        output_list = self.run_testcase(self.extracted_code)
        if len(output_list['fail_list']) == 0:
            logger.info('恭喜用例通过')
            return True
        else:
            while len(output_list['fail_list']) != 0 and self.curr_debug_num < self.max_debug_num:
                self.curr_debug_num += 1
                fail_list = output_list['fail_list']
                logger.info(f'代码出错啦,这是第{self.curr_debug_num}次debug')
                base_info.extend([{'role':'assistant','content':self.response},
                                  {'role':'user','content':f'你的代码出错啦！输入是{fail_list[0]},输出是{fail_list[1]},期望输出是{fail_list[2]}'}])
                self.response = self.get_response(base_info)
                extracted_code = self.extract_code(self.response)
                output_list = self.run_testcase(extracted_code)
            if len(output_list['fail_list']) != 0:
                logger.info('很遗憾，模型无法满足您的需求')
                print(f'base_info是:{base_info}')
                return False
            else:
                logger.info(f'运气不错,历经{self.curr_debug_num}次磨难总算成功！')
                return True






        
if __name__ =='__main__':
    question = '''
# [NOIP2005 普及组] 陶陶摘苹果

## 题目描述

陶陶家的院子里有一棵苹果树，每到秋天树上就会结出 $10$ 个苹果。苹果成熟的时候，陶陶就会跑去摘苹果。陶陶有个 $30$ 厘米高的板凳，当她不能直接用手摘到苹果的时候，就会踩到板凳上再试试。


现在已知 $10$ 个苹果到地面的高度，以及陶陶把手伸直的时候能够达到的最大高度，请帮陶陶算一下她能够摘到的苹果的数目。假设她碰到苹果，苹果就会掉下来。

## 输入格式

输入包括两行数据。第一行包含 $10$ 个 $100$ 到 $200$ 之间（包括 $100$ 和 $200$）的整数（以厘米为单位）分别表示 $10$ 个苹果到地面的高度，两个相邻的整数之间用一个空格隔开。第二行只包括一个 $100$ 到 $120$ 之间（包含 $100$ 和 $120$）的整数（以厘米为单位），表示陶陶把手伸直的时候能够达到的最大高度。

## 输出格式

输出包括一行，这一行只包含一个整数，表示陶陶能够摘到的苹果的数目。

## 样例 #1

### 样例输入 #1

```
100 200 150 140 129 134 167 198 200 111
110
```

### 样例输出 #1

```
5
```

## 提示

**【题目来源】**

NOIP 2005 普及组第一题
    '''
    input = '''
100 200 150 140 129 134 167 198 200 111
110
    '''
    output = '5'
    model_name = 'gpt-3.5-turbo'
    openai_apikey = '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'
    codeagent = CodeAgent(model_name,openai_apikey)
    codeagent.add_testcase('''100 200 150 140 129 134 167 198 200 111
110''','''5''')
    codeagent.runpipling(question)
