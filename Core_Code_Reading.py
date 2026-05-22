import os
import asyncio
import re
import subprocess

import fire
from Main import API
from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.roles.role import Role, RoleReactMode
from metagpt.schema import Message
from Main import File_path
os.environ["ZHIPUAI_API_KEY"] = API
folder_path = File_path
# 定义函数read_files，用于读取指定文件夹中的所有文件内容，并将读取的结果返回。
def read_files(folder_path):
    # 初始化一个空字符串context，用于存储读取的文件内容。
    context = ""
    # 遍历folder_path文件夹中的所有文件名。
    for filename in os.listdir(folder_path):
        # 获取文件的完整路径。
        file_path = os.path.join(folder_path, filename)
        # 判断file_path是否是一个文件。
        if os.path.isfile(file_path):
            # 向context中添加文件名和文件内容。
            context += f"File: {filename}\n"
            try:
                # 以只读模式打开文件，并读取文件内容。
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 将文件内容添加到context中。
                    context += content + "\n\n" + "=" * 50 + "\n\n"
            except Exception as e:
                # 如果读取文件出错，将错误信息添加到context中。
                context += f"Error reading {filename}: {str(e)}\n\n" + "=" * 50 + "\n\n"

    # 返回context字符串。
    return context

# 调用函数，读取指定文件夹中的文件内容。
context = read_files(folder_path)
# SimpleWriteCode 类是用于解析核心代码的类
class SimpleWriteCode(Action):
    # 定义了一个格式化字符串，用于生成代码解析文档的模板
    PROMPT_TEMPLATE: str = """
     对{instruction}中的每段核心代码分析并分别生成代码解析文档按照以下五点要求：
    0.具体的代码描述，详细一点
    1.方法：常用的方法就是下面的四种：结构、功能、输入、输出
    2.url
    3.请求参数和返回参数：请求参数和返回参数都分为：字段、说明、类型、备注、是否必填这5列。字段：类的属性，说明：中文释义，类型：属性的类型，只有String、Number、Object、Array四大类，备注：一些解释语，或者写简单的示例
    4.返回参数，要分两种情况讨论：只返回接口调用成功或者失败：code、reason，返回参数：字段、类型
    对每段代码分别按以上要求生成一篇代码解读文档，尽可能详细，用中文回答
    Return ```python your_code_here ``` with NO other texts,
    your code:
    """

    # 定义了类的名称
    name: str = "SimpleWriteCode"

    # 定义了一个异步方法，用于执行代码解析操作
    async def run(self, instruction: str):
        # 使用格式化字符串生成请求内容
        prompt = self.PROMPT_TEMPLATE.format(instruction=instruction)

        # 异步调用_aask方法，传入请求内容并获取响应
        rsp = await self._aask(prompt)

        # 使用静态方法解析响应内容，提取代码文本
        code_text = SimpleWriteCode.parse_code(rsp)

        # 返回提取到的代码文本
        return code_text

    # 定义了一个静态方法，用于解析响应内容
    @staticmethod
    def parse_code(rsp):
        # 定义了一个正则表达式模式，用于匹配代码块
        pattern = r"```python(.*)```"
        # 使用正则表达式搜索响应内容中的代码块
        match = re.search(pattern, rsp, re.DOTALL)
        # 如果找到代码块，则提取代码文本，否则直接返回响应内容
        code_text = match.group(1) if match else rsp
        # 返回提取到的代码文本
        return code_text

# 这是 SimpleRunCode 类，它继承自 Action 类
class SimpleRunCode(Action):
    # 设置类的名称属性，默认为 "SimpleRunCode"
    name: str = "SimpleRunCode"

    # 定义一个异步函数 run，用于执行代码
    async def run(self, code_text: str):
        # 使用 subprocess.run 函数执行传入的代码
        # 参数 ["python3", "-c", code_text] 表示使用 python3 命令执行单行代码
        # capture_output=True 表示捕获输出，text=True 表示输出以文本形式返回
        result = subprocess.run(["python3", "-c", code_text], capture_output=True, text=True)
        # 获取执行结果的标准输出
        code_result = result.stdout
        # 使用 logger 记录执行结果
        logger.info(f"{code_result=}")
        # 返回执行结果
        return code_result


# 定义一个名为SimpleCoder的类，该类继承自Role类
class SimpleCoder(Role):
    # SimpleCoder类的name属性，默认为"Alice"
    name: str = "Alice"
    # SimpleCoder类的profile属性，默认为"SimpleCoder"
    profile: str = "SimpleCoder"

    # SimpleCoder类的构造函数
    def __init__(self, **kwargs):
        # 调用父类Role的构造函数，传递不定参数**kwargs
        super().__init__(**kwargs)
        # 为SimpleCoder实例设置动作，这里只设置了一个动作SimpleWriteCode
        self.set_actions([SimpleWriteCode])

    async def _act(self) -> Message:
        # 使用logger记录信息，输出当前设置和待办事项的名称
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        # 获取当前待办事项，这里预期是SimpleWriteCode实例
        todo = self.rc.todo  # todo将会是SimpleWriteCode()

        # 获取记忆中的最新消息
        msg = self.get_memories(k=1)[0]  # find the most recent messages
        # 等待待办事项运行完毕，并获取生成的代码文本
        code_text = await todo.run(msg.content)
        # 创建一个新的Message实例，内容为生成的代码文本，角色为SimpleCoder，由待办事项触发
        msg = Message(content=code_text, role=self.profile, cause_by=type(todo))

        # 返回生成的消息
        return msg


# 定义一个名为RunnableCoder的类，该类继承自Role类
class RunnableCoder(Role):
    # 定义属性name，其类型为str，默认值为"Alice"
    name: str = "Alice"
    # 定义属性profile，其类型为str，默认值为"RunnableCoder"
    profile: str = "RunnableCoder"

    # 定义构造函数，用于初始化对象
    def __init__(self, **kwargs):
        # 调用父类Role的构造函数，传递**kwargs参数，以便继承父类的属性或方法
        super().__init__(**kwargs)
        # 设置角色的动作，这里添加了两个动作：SimpleWriteCode和SimpleRunCode
        self.set_actions([SimpleWriteCode, SimpleRunCode])
        # 设置反应模式为按顺序反应，值为RoleReactMode.BY_ORDER.value
        self._set_react_mode(react_mode=RoleReactMode.BY_ORDER.value)

    # 定义一个异步方法_act，用于执行角色的动作
    async def _act(self) -> Message:
        # 记录日志信息，打印角色配置和待办事项名称
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        # 在此选择按顺序执行的动作
        # 待办事项将首先执行SimpleWriteCode()，然后执行SimpleRunCode()
        todo = self.rc.todo

        # 获取最近的k条记忆信息，此处k=1，取第一条信息
        msg = self.get_memories(k=1)[0]  # find the most k recent messages
        # 异步执行待办事项run方法，传入msg.content作为参数
        result = await todo.run(msg.content)

        # 创建一个新的Message对象，设置其内容为运行结果，角色为RunnableCoder，原因由待办事项类型表示
        msg = Message(content=result, role=self.profile, cause_by=type(todo))
        # 将新消息添加到记忆中
        self.rc.memory.add(msg)
        # 返回新的消息对象
        return msg

def main(msg=context):
    # role = SimpleCoder()
    role = RunnableCoder()
    logger.info(msg)
    result = asyncio.run(role.run(msg))
    return result
if __name__ == "__main__":
    fire.Fire(main)