# -*- coding : utf-8 -*-
import streamlit as st
import time
from loguru import logger
import io
from ai_tool_demo import CodeAgent

log_stream = io.StringIO()
class StreamlitSink:
    def write(self,message):
        log_stream.write(message)
    def flush(self):
        pass
logger.remove()
logger.add(StreamlitSink(),format = '{time:YYYY-MM-DD HH:mm:ss}|{level}|{message}')

if 'log_content' not in st.session_state:
    st.session_state.log_content = []
    st.session_state.last_log_time = time.time()

if 'test_case' not in st.session_state:
    st.session_state.test_case = []

st.title('小花的AI代码助手')

with st.sidebar:
    model_name = st.selectbox('选择你的模型',['gpt-3.5-turbo','gpt-4','gpt-4-turbo'])
    api_key = st.text_input('请输入你的api_key(open_ai)',type = 'password')

if api_key:
    codeagent = CodeAgent(model_name,api_key)
else:
    st.error('请输入api_key')
    st.stop()

question = st.text_area('请输入您的问题',height = 300)

st.write('添加测试用例')

input_area,output_area = st.columns(2)
with input_area:
    input_text = st.text_area('输入',height = 100,key = 'input_area')
with output_area:
    expected_output = st.text_area('期望输出',height = 100,key = 'expected_output')

input_button,clear_button = st.columns(2)
with input_button:
    if st.button('添加用例'):
        st.session_state.test_case.append([input_text.strip(),expected_output.strip()])
        st.success('添加用例成功')
with clear_button:
    if st.button('清除用例'):
        st.session_state.test_case = []
        st.warning('清除用例成功')

st.write('已添加的用例')
for idx,content in enumerate(st.session_state.test_case):
    st.write(f'测试用例{idx+1}: \n输入:{content[0]}\n期望输出:{content[1]}')


if st.button('生成代码'):
    if len(st.session_state.test_case) > 1:
        st.error('添加用例过多，单次只能处理一个用例')
        st.stop()
    for case in st.session_state.test_case:
        codeagent.add_testcase(case[0],case[1])
    flag = codeagent.runpipling(question)

    current_time = time.time()
    if current_time - st.session_state.last_log_time > 1:
        st.session_state.log_content = log_stream.getvalue()
        st.session_state.last_log_time = current_time

    st.markdown('## 代码运行日志')
    st.markdown(st.session_state.log_content)
    if hasattr(codeagent,'extracted_code'):
        if flag:
            st.success(f'{model_name}幸不辱命!成功通过用例')
        else:
            st.warning(f'{model_name}还没有能力处理这么复杂的题目o(╥﹏╥)o')
        st.markdown('## 最终结果')
        st.code(codeagent.extracted_code,language = 'python')






