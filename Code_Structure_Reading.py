import asyncio
import os

import re
import subprocess
import fire

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.roles.role import Role, RoleReactMode
from metagpt.schema import Message
from Main import API
from Main import File_path
os.environ["ZHIPUAI_API_KEY"] = API
folder_path = File_path
def read_files_in_folder(folder_path):
    """
    读取指定文件夹中的所有文件内容，并将它们拼接成一个长字符串返回。

    Args:
        folder_path (str): 要读取文件的文件夹路径。

    Returns:
        str: 包含所有文件内容的字符串，每个文件内容之间用特定分隔符分隔。
    """
    context = ""  # 初始化一个空字符串，用于存储所有文件的内容
    for filename in os.listdir(folder_path):  # 遍历指定文件夹中的所有文件和目录
        file_path = os.path.join(folder_path, filename)  # 构建文件的完整路径
        if os.path.isfile(file_path):  # 检查路径是否指向一个文件
            context += f"File: {filename}\n"  # 在上下文中添加文件名作为标记
            try:
                with open(file_path, 'r', encoding='utf-8') as f:  # 以只读模式打开文件，并指定编码为utf-8
                    content = f.read()  # 读取文件内容
                    context += content + "\n\n" + "=" * 50 + "\n\n"  # 将文件内容添加到上下文中，并用50个等号作为分隔符
            except Exception as e:  # 如果在读取文件时发生异常
                context += f"Error reading {filename}: {str(e)}\n\n" + "=" * 50 + "\n\n"  # 将错误信息添加到上下文中，并用50个等号作为分隔符

    return context  # 返回包含所有文件内容的字符串


# 指定要读取文件的文件夹路径

# 调用函数并获取结果
context = read_files_in_folder(folder_path)
# 此时，context变量包含了指定文件夹中所有文件的内容，每个文件内容之间用特定的分隔符分隔。



class SimpleWriteCode(Action):
    """
    一个简单的代码生成类，用于根据指令生成数据结构报告。
    """
    PROMPT_TEMPLATE: str = """  
     对{instruction}中的每个类分析并分别生成数据结构报告按照以下结构要求：  
    一.数据结构包含的各个变量    
    1. 变量名称  
    2. 变量编号id    
    3. 变量类型: 阐明变量类型, 如整形, 浮点型等  
    4. 介绍: 变量作用  
    二. 数据结构作用  
    阐述这一整个数据结构的作用  
    对每个类分别按以上要求生成一篇核心数据结构报告，详细一点，用中文回答  
    Return   
    """
    """  
    定义了一个模板，用于指导如何生成数据结构报告的提示信息。  
    """

    name: str = "SimpleWriteCode"
    """  
    类的名称。  
    """

    async def run(self, instruction: str):
        """
        异步执行函数，根据给定的指令生成数据结构报告。

        Args:
            instruction (str): 需要分析并生成报告的指令或说明。

        Returns:
            str: 生成的代码文本或数据结构报告内容。
        """
        prompt = self.PROMPT_TEMPLATE.format(instruction=instruction)
        """  
        将指令填充到模板中，生成提示信息。  
        """

        rsp = await self._aask(prompt)
        """  
        通过某种方式（假设_aask是异步提问或查询的方法）获取响应。  
        """

        code_text = SimpleWriteCode.parse_code(rsp)
        """  
        调用静态方法parse_code来解析响应中的代码或报告内容。  
        """

        return code_text

    @staticmethod
    def parse_code(rsp):
        """
        静态方法，用于从响应中解析并提取代码文本。

        Args:
            rsp (str): 响应的字符串，可能包含代码或其他信息。

        Returns:
            str: 提取的代码文本，如果未找到则可能返回原始响应。
        """
        pattern = r"```python(.*)```"
        """  
        定义正则表达式模式，用于匹配`python`代码块。  
        """

        match = re.search(pattern, rsp, re.DOTALL)
        """  
        使用正则表达式在响应中搜索匹配项，re.DOTALL使`.`能匹配包括换行符在内的任意字符。  
        """

        code_text = match.group(1) if match else rsp
        """  
        如果找到匹配项，则提取并返回代码文本；否则，返回原始响应。  
        """

        return code_text

class SimpleRunCode(Action):
        """
        一个简单的代码运行类，用于执行给定的Python代码文本。
        """
        name: str = "SimpleRunCode"
        """  
        类的名称，标识这个Action是用于运行代码的。  
        """

        async def run(self, code_text: str):
            """
            异步执行函数，用于运行给定的Python代码文本。

            Args:
                code_text (str): 需要执行的Python代码文本。

            Returns:
                str: 执行代码后，标准输出的内容。
            """
            # 使用subprocess.run执行外部命令，这里是运行python3解释器并传入-c选项以执行给定的代码文本
            result = subprocess.run(["python3", "-c", code_text], capture_output=True, text=True)
            """  
            subprocess.run执行命令并等待完成。  
            - ["python3", "-c", code_text] 是命令和参数的列表。  
            - capture_output=True 表示捕获命令的标准输出和标准错误输出。  
            - text=True 表示将输出作为文本（str）处理，而不是字节（bytes）。  
            """

            code_result = result.stdout
            """  
            从执行结果中提取标准输出内容。  
            """

            # 假设这里有一个logger对象已经配置好，用于记录日志
            logger.info(f"{code_result=}")
            """  
            使用logging模块的logger对象记录执行结果的信息。  
            这里使用了f-string和等号操作符来生成日志消息，以便于阅读。  
            """

            return code_result
            """  
            返回执行代码后的标准输出内容。  
            """


class SimpleCoder(Role):
    """
    简单编码者角色类，用于执行代码生成任务。
    """
    name: str = "Alice"
    """  
    角色的名称。  
    """
    profile: str = "SimpleCoder"
    """  
    角色的描述或标签。  
    """

    def __init__(self, **kwargs):
        """
        初始化SimpleCoder实例。

        Args:
            **kwargs: 关键字参数，用于传递给父类Role的构造函数。
        """
        super().__init__(**kwargs)
        # 设置该角色可以执行的动作列表，这里只包含SimpleWriteCode动作
        self.set_actions([SimpleWriteCode])

    async def _act(self) -> Message:
        """
        执行角色的行为，这里是生成代码文本。

        Returns:
            Message: 包含生成代码文本的消息对象。
        """
        # 记录日志，显示角色正在执行的任务
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")

        # 获取当前要执行的任务，这里假设是SimpleWriteCode实例
        todo = self.rc.todo

        # 从记忆中获取最近的一条消息作为输入（这里假设存在get_memories方法）
        msg = self.get_memories(k=1)[0]

        # 执行任务（SimpleWriteCode的run方法），传入消息内容作为输入
        code_text = await todo.run(msg.content)

        # 创建一个新的消息对象，包含生成的代码文本、角色描述和触发动作的类型
        msg = Message(content=code_text, role=self.profile, cause_by=type(todo))

        # 返回包含生成代码的消息对象
        return msg


class RunnableCoder(Role):
    """
    可运行编码者角色类，能够按顺序执行编写和运行代码的任务。
    """
    name: str = "Alice"
    """  
    角色的名称。  
    """
    profile: str = "RunnableCoder"
    """  
    角色的描述或标签。  
    """

    def __init__(self, **kwargs):
        """
        初始化RunnableCoder实例。

        Args:
            **kwargs: 关键字参数，用于传递给父类Role的构造函数。
        """
        super().__init__(**kwargs)
        # 设置该角色可以执行的动作列表，这里包含编写和运行代码的动作
        self.set_actions([SimpleWriteCode, SimpleRunCode])
        # 设置反应模式为按顺序执行，即先执行SimpleWriteCode，然后执行SimpleRunCode
        self._set_react_mode(react_mode=RoleReactMode.BY_ORDER.value)

    async def _act(self) -> Message:
        """
        执行角色的行为，这里是按顺序编写和运行代码。

        Returns:
            Message: 包含执行结果的消息对象。
        """
        # 记录日志，显示角色正在执行的任务
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")

        # 注意：这里实际上有一个问题，因为self.rc.todo只会是列表中的一个动作实例，
        # 但由于我们设置了反应模式为按顺序执行，所以需要在外部逻辑中控制执行顺序。
        # 这里我们假设_act方法会被外部逻辑调用多次，每次调用处理一个动作。

        # 假设当前self.rc.todo已经根据外部逻辑被设置为SimpleWriteCode或SimpleRunCode
        todo = self.rc.todo

        # 从记忆中获取最近的一条消息作为输入
        msg = self.get_memories(k=1)[0]

        # 注意：这里我们直接调用todo.run，但实际上应该有一个机制来区分是编写还是运行代码
        # 这里为了简化，我们假设run方法能够处理两种情况（实际中可能需要重写或修改）
        # 或者，外部逻辑已经确保了todo是当前应该执行的动作实例
        result = await todo.run(msg.content)

        # 创建一个新的消息对象，包含执行结果、角色描述和触发动作的类型
        msg = Message(content=result, role=self.profile, cause_by=type(todo))

        # 将新消息添加到记忆中
        self.rc.memory.add(msg)

        # 返回包含执行结果的消息对象
        return msg


# main 函数，用于处理命令行输入和启动异步任务
def main(msg=context):

    # 创建 RunnableCoder 实例
    role = RunnableCoder()

    # 记录输入的消息
    logger.info(msg)

    # 异步运行 run 方法，并等待结果
    result = asyncio.run(role.run(msg))

    # 记录结果
    return result


if __name__ == "__main__":


    # 使用 fire.Fire 将 main 函数暴露为命令行接口
    # 这允许用户通过命令行传递参数给 main 函数
    fire.Fire(main)