import dashscope
from http import HTTPStatus

# 把你刚才复制的 Key 填在这里
dashscope.api_key = "sk-588a2db89b454327ad4cc1a43ffedc7c"


def simple_test():
    messages = [{'role': 'user', 'content': '你好，你是谁？'}]

    # 调用通义千问-Turbo 模型测试一下对话
    response = dashscope.Generation.call(
        model='qwen-turbo',
        messages=messages
    )

    if response.status_code == HTTPStatus.OK:
        print("测试成功！AI回复：")
        print(response.output.text)
    else:
        print("测试失败，请检查Key或网络。")
        print(response)


if __name__ == '__main__':
    simple_test()