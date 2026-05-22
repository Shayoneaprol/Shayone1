import os
import asyncio
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
    context = ""
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            context += f"File: {filename}\n"
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    context += content + "\n\n" + "=" * 50 + "\n\n"
            except Exception as e:
                context += f"Error reading {filename}: {str(e)}\n\n" + "=" * 50 + "\n\n"

    return context



context = read_files_in_folder(folder_path)


class SimpleWriteCode(Action):
    PROMPT_TEMPLATE: str = """
     对{instruction}中的每个接口分析并分别生成接口文档按照以下五点要求：
    0.具体的接口描述，详细一点
    1.方法：常用的方法就是下面的四种：GET PUT POST DELETE

    2.url

    3.请求参数和返回参数：请求参数和返回参数都分为：字段、说明、类型、备注、是否必填这5列。字段：类的属性，说明：中文释义，类型：属性的类型，只有String、Number、Object、Array四大类，备注：一些解释语，或者写简单的示例

    4.返回参数，要分两种情况讨论：只返回接口调用成功或者失败：code、reason，返回参数：字段、类型
    对每个接口分别按以上要求生成一篇接口文档，详细一点，用中文回答
    Return ```python your_code_here ``` with NO other texts,
    your code:
    """

    name: str = "SimpleWriteCode"

    async def run(self, instruction: str):
        prompt = self.PROMPT_TEMPLATE.format(instruction=instruction)

        rsp = await self._aask(prompt)

        code_text = SimpleWriteCode.parse_code(rsp)

        return code_text

    @staticmethod
    def parse_code(rsp):
        pattern = r"```python(.*)```"
        match = re.search(pattern, rsp, re.DOTALL)
        code_text = match.group(1) if match else rsp
        return code_text


class SimpleRunCode(Action):
    name: str = "SimpleRunCode"

    async def run(self, code_text: str):
        result = subprocess.run(["python3", "-c", code_text], capture_output=True, text=True)
        code_result = result.stdout
        logger.info(f"{code_result=}")
        return code_result


class SimpleCoder(Role):
    name: str = "Alice"
    profile: str = "SimpleCoder"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([SimpleWriteCode])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo  # todo will be SimpleWriteCode()

        msg = self.get_memories(k=1)[0]  # find the most recent messages
        code_text = await todo.run(msg.content)
        msg = Message(content=code_text, role=self.profile, cause_by=type(todo))

        return msg


class RunnableCoder(Role):
    name: str = "Alice"
    profile: str = "RunnableCoder"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([SimpleWriteCode, SimpleRunCode])
        self._set_react_mode(react_mode=RoleReactMode.BY_ORDER.value)

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        # By choosing the Action by order under the hood
        # todo will be first SimpleWriteCode() then SimpleRunCode()
        todo = self.rc.todo

        msg = self.get_memories(k=1)[0]  # find the most k recent messages
        result = await todo.run(msg.content)

        msg = Message(content=result, role=self.profile, cause_by=type(todo))
        self.rc.memory.add(msg)
        return msg


def main(msg=context):
    # role = SimpleCoder()
    role = RunnableCoder()
    logger.info(msg)
    result = asyncio.run(role.run(msg))
    return result
    


if __name__ == "__main__":
    fire.Fire(main)