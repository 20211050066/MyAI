import os
from pathlib import Path
from openai import OpenAI


class AIAgent:
    """AI编程助手核心业务逻辑类"""

    def __init__(self, prompt_dir: str = None):
        """
        初始化OpenAI客户端和提示词

        Args:
            prompt_dir: 提示词文件目录路径，默认为当前脚本下的Prompt目录
        """
        # self.client = OpenAI(
        #     api_key=os.environ.get('DEEPSEEK_API_KEY'),
        #     base_url="https://api.deepseek.com"
        # )
        self.client = OpenAI(
            api_key="ollama",
            base_url="http://localhost:11434/v1"
        )

        # 默认配置
        self.default_language = 'Python'
        self.default_character = """- **专业且平易近人**：使用"我们通常建议这样做..."代替生硬的"你必须..."。
- **简洁**：解释代码为什么要这样写，而不是逐行翻译显而易见的语法。
- **主动避坑**：像一位 Code Review 同事一样，主动指出代码中可能未被察觉的隐患。"""

        # 设置提示词目录
        if prompt_dir is None:
            self.prompt_dir = Path(__file__).parent / "Prompt"
        else:
            self.prompt_dir = Path(prompt_dir)

        # 缓存提示词模板
        self._prompt_cache = {}

        # 加载提示词模板
        self._load_prompt_templates()

    def _load_prompt_templates(self):
        """
        从文件加载所有提示词模板并缓存
        """
        prompt_files = {
            'base': 'base.txt',
            'format': 'format.txt',
            'tools': 'tools.txt'
        }

        for key, filename in prompt_files.items():
            file_path = self.prompt_dir / filename
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._prompt_cache[key] = f.read()
                print(f"[AIAgent] 成功加载提示词: {filename}")
            except FileNotFoundError:
                print(f"[AIAgent] 警告: 未找到提示词文件 {filename}")
                self._prompt_cache[key] = ""
            except Exception as e:
                print(f"[AIAgent] 错误: 读取 {filename} 失败 - {str(e)}")
                self._prompt_cache[key] = ""

    def build_system_prompt(self, language: str = None, character: str = None) -> str:
        """
        构建系统提示词（从多个文件组合）

        Args:
            language: 编程语言，默认为实例的 default_language
            character: 语气与风格描述，默认为实例的 default_character

        Returns:
            格式化后的完整系统提示词
        """
        if language is None:
            language = self.default_language
        if character is None:
            character = self.default_character

        # 获取各个部分的提示词
        base_prompt = self._prompt_cache.get('base', '')
        format_prompt = self._prompt_cache.get('format', '')
        tools_prompt = self._prompt_cache.get('tools', '')

        # 格式化基础提示词（填充语言和性格）
        formatted_base = base_prompt % (language, character)

        # 组合所有提示词
        full_prompt = f"{formatted_base}\n\n{format_prompt}\n\n{tools_prompt}"

        return full_prompt

    def chat(self, messages: list, system_prompt: str, stream: bool = True):
        """
        与AI模型进行对话

        Args:
            messages: 历史消息列表
            system_prompt: 系统提示词
            stream: 是否使用流式返回

        Returns:
            流式响应迭代器或非流式响应对象
        """
        full_messages = [
            {"role": "system", "content": system_prompt},
            *messages
        ]

        response = self.client.chat.completions.create(
            model="deepseek-r1:8b",
            messages=full_messages,
            stream=stream
        )

        return response

    def get_stream_response(self, response):
        """
        处理流式响应，逐步获取内容

        Args:
            response: 流式响应对象

        Yields:
            每次迭代的完整响应内容
        """
        full_response = ""
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                full_response += content
                yield full_response

    def get_default_config(self):
        """
        获取默认配置

        Returns:
            包含默认语言和性格配置的字典
        """
        return {
            'language': self.default_language,
            'character': self.default_character
        }

    def reload_prompts(self):
        """
        重新加载提示词文件（用于热更新）
        """
        self._prompt_cache.clear()
        self._load_prompt_templates()
        print("[AIAgent] 提示词已重新加载")


class APIAgent(AIAgent):
    """使用API的AI编程助手核心业务逻辑类"""
    def __init__(self, prompt_dir: str = None):
        super().__init__(prompt_dir)
        self.client = OpenAI(
            api_key=os.environ.get('QW_API_KEY'),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

        # 加载会话标题生成提示词
        self._load_session_title_prompt()

    def _load_session_title_prompt(self):
        """
        加载会话标题生成提示词
        """
        title_prompt_file = self.prompt_dir / "get_session_context.txt"
        try:
            with open(title_prompt_file, 'r', encoding='utf-8') as f:
                self.session_title_prompt = f.read()
            print(f"[APIAgent] 成功加载会话标题提示词")
        except FileNotFoundError:
            print(f"[APIAgent] 警告: 未找到会话标题提示词文件 get_session_context.txt")
            self.session_title_prompt = self._get_default_title_prompt()
        except Exception as e:
            print(f"[APIAgent] 错误: 读取会话标题提示词失败 - {str(e)}")
            self.session_title_prompt = self._get_default_title_prompt()

    @staticmethod
    def _get_default_title_prompt():
        """
        获取默认的会话标题提示词（备用方案）
        """
        return """你是一个专业的会话标题提炼助手。请根据用户提供的第一条问题和AI助手的第一条回复，提炼出一个简洁、准确的会话标题。

    要求：
    1. 标题长度控制在15-20个字符以内
    2. 准确概括对话的核心主题
    3. 简洁明了，便于用户快速识别
    4. 不要使用标点符号结尾
    5. 直接返回标题，不要有任何解释

    示例：
    - 用户问："如何用Python实现快速排序？" → 标题："Python快速排序实现"
    - 用户问："帮我优化这段数据库查询代码" → 标题："数据库查询优化"
    - 用户问："React中如何使用useEffect钩子？" → 标题："React useEffect用法"
    """

    def generate_session_title(self, first_user_msg: str, first_assistant_msg: str) -> str:
        """
        使用DeepSeek生成会话标题

        Args:
            first_user_msg: 第一条用户消息
            first_assistant_msg: 第一条AI回复

        Returns:
            生成的会话标题
        """
        try:
            # 构建用户提示词
            user_prompt = f"用户问题：{first_user_msg}\n\nAI回复：{first_assistant_msg}"
            # print(f"[APIAgent] 提示词：{user_prompt}")
            # 调用DeepSeek API
            response = self.chat(
                messages=[{"role": "user", "content": user_prompt}],
                system_prompt=self.session_title_prompt,
                stream=False
            )

            # 获取响应内容
            title = response.choices[0].message.content.strip()
            print(f"[APIAgent] 生成的会话标题：{title}")

            # 清理标题（去除可能的引号、句号等）
            title = title.strip('"\'。！？')

            # 确保标题长度合理
            if len(title) > 30:
                title = title[:30]

            return title if title else "新会话"

        except Exception as e:
            print(f"[APIAgent] 生成会话标题失败: {str(e)}")
            return "新会话"

    def chat(self, messages: list, system_prompt: str, stream: bool = True):
        """
        与AI模型进行对话

        Args:
            messages: 历史消息列表
            system_prompt: 系统提示词
            stream: 是否使用流式返回

        Returns:
            流式响应迭代器或非流式响应对象
        """
        full_messages = [
            {"role": "system", "content": system_prompt},
            *messages
        ]
        response = self.client.chat.completions.create(
            model="qwen3-max",
            messages=full_messages,
            stream=stream
        )

        return response