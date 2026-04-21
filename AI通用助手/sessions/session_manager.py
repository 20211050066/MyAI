import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid


class SessionManager:
    """会话管理器 - 负责会话的创建、保存、加载和删除"""

    def __init__(self, data_dir: str = None, agent = None):
        """
        初始化会话管理器

        Args:
            data_dir: 会话数据存储目录，默认为当前脚本下的sessions/data目录
            agent: AIAgent实例，用于生成会话标题
        """
        if data_dir is None:
            self.data_dir = Path(__file__).parent / "data"
        else:
            self.data_dir = Path(data_dir)

        self.agent = agent

        # 确保数据目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def generate_session_title_with_ai(self, messages: list) -> str:
        """
        使用大模型提炼会话标题

        Args:
            messages: 消息列表

        Returns:
            提炼后的会话标题字符串
        """
        if not self.agent:
            return self._generate_simple_title(messages)

        if not messages or len(messages) < 1:
            return "新会话"

        # 提取第一条用户消息和第一条AI回复
        first_user_msg = ""
        first_assistant_msg = ""

        for msg in messages:
            if msg.get("role") == "user" and not first_user_msg:
                first_user_msg = msg.get("content", "").strip()
            elif msg.get("role") == "assistant" and not first_assistant_msg:
                first_assistant_msg = msg.get("content", "").strip()

            if first_user_msg and first_assistant_msg:
                break

        # 如果没有任何消息，返回默认标题
        if not first_user_msg and not first_assistant_msg:
            return "新会话"

        # 检查是否是 APIAgent，使用专用方法
        from Agent import APIAgent
        if isinstance(self.agent, APIAgent):
            try:
                print("[SessionManager] 使用APIAgent生成标题")
                return self.agent.generate_session_title(first_user_msg, first_assistant_msg)
            except Exception as e:
                print(f"[SessionManager] APIAgent生成标题失败: {str(e)}，使用备用方法")

        # 对于其他类型的 Agent，使用通用方法
        try:
            # 构建用于提炼标题的系统提示词
            system_prompt = """你是一个专业的会话标题提炼助手。请根据用户提供的第一条问题和AI助手的第一条回复，提炼出一个简洁、准确的会话标题。

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

            # 构建用户提示词
            user_prompt = f"用户问题：{first_user_msg[:200]}\n\nAI回复：{first_assistant_msg[:200]}"

            # 调用大模型（非流式）
            response = self.agent.chat(
                messages=[{"role": "user", "content": user_prompt}],
                system_prompt=system_prompt,
                stream=False
            )

            # 获取响应内容
            title = response.choices[0].message.content.strip()

            # 清理标题（去除可能的引号、句号等）
            title = title.strip('"\'。！？')

            # 确保标题长度合理
            if len(title) > 30:
                title = title[:30]

            return title if title else self._generate_simple_title(messages)
        except Exception as e:
            print(f"[SessionManager] 使用AI生成标题失败: {str(e)}，使用简单方法替代")
            return self._generate_simple_title(messages)

    @staticmethod
    def _generate_simple_title(messages: list) -> str:
        """
        使用简单方法生成会话标题（备用方案）

        Args:
            messages: 消息列表

        Returns:
            会话标题字符串
        """
        if not messages:
            return "新会话"

        # 获取第一条用户消息作为标题基础
        for msg in messages:
            if msg.get("role") == "user":
                content = msg.get("content", "").strip()
                if content:
                    # 截取前20个字符作为标题
                    title = content[:20]
                    # 如果内容超过20字符，添加省略号
                    if len(content) > 20:
                        title += "..."
                    return title

        # 如果没有用户消息，使用第一条AI回复
        for msg in messages:
            if msg.get("role") == "assistant":
                content = msg.get("content", "").strip()
                if content:
                    title = content[:20]
                    if len(content) > 20:
                        title += "..."
                    return title

        return "新会话"

    def create_session(self, session_id: str = None) -> dict:
        """
        创建新会话

        Args:
            session_id: 会话ID，不传则自动生成

        Returns:
            新会话字典
        """
        if session_id is None:
            session_id = self.generate_current_session_id()

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        session = {
            "session_id": session_id,
            "created_at": now,
            "updated_at": now,
            "messages": []
        }

        return session

    def save_session(self, session: dict) -> str:
        """
        保存会话到文件

        Args:
            session: 会话字典

        Returns:
            保存的文件路径
        """
        session_id = session.get("session_id")
        if not session_id:
            raise ValueError("会话缺少session_id")

        # 更新更新时间
        session["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 使用AI生成或更新会话标题（如果有agent且没有标题）
        if self.agent and ("title" not in session or not session.get("title")):
            session["title"] = self.generate_session_title_with_ai(session.get("messages", []))
        elif "title" not in session or not session.get("title"):
            # 备用方案：使用简单方法生成标题
            session["title"] = self._generate_simple_title(session.get("messages", []))

        # 构建文件路径
        file_path = self.data_dir / f"{session_id}.json"
        # 如果文件不存在，则创建
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(session, f, ensure_ascii=False, indent=2)

        return str(file_path)

    def load_session(self, session_id: str) -> Optional[dict]:
        """
        从文件加载会话

        Args:
            session_id: 会话ID

        Returns:
            会话字典，如果不存在返回None
        """
        file_path = self.data_dir / f"{session_id}.json"

        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                session = json.load(f)
            return session
        except Exception as e:
            print(f"[SessionManager] 加载会话失败: {str(e)}")
            return None

    def delete_session(self, session_id: str) -> bool:
        """
        删除会话文件

        Args:
            session_id: 会话ID

        Returns:
            是否删除成功
        """
        file_path = self.data_dir / f"{session_id}.json"

        if not file_path.exists():
            return False

        try:
            file_path.unlink()
            return True
        except Exception as e:
            print(f"[SessionManager] 删除会话失败: {str(e)}")
            return False

    def list_sessions(self, reverse: bool = True) -> list:
        """
        列出所有会话

        Args:
            reverse: 是否倒序（最新的在前）

        Returns:
            会话信息列表（包含session_id和title）
        """
        sessions = []

        if os.path.exists(self.data_dir):
            for file_name in os.listdir(self.data_dir):
                if file_name.endswith(".json"):
                    session_id = file_name[:-5]
                    # 读取文件获取标题
                    file_path = self.data_dir / file_name
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            session_data = json.load(f)
                            title = session_data.get("title", "新会话")
                            sessions.append({
                                "session_id": session_id,
                                "title": title,
                                "updated_at": session_data.get("updated_at", "")
                            })
                    except Exception as e:
                        # 如果读取失败，使用默认值
                        sessions.append({
                            "session_id": session_id,
                            "title": "新会话",
                            "updated_at": ""
                        })

        # 按更新时间排序
        sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=reverse)

        return sessions

    def auto_save_session(self, session: dict) -> str:
        """
        自动保存会话（如果session_id不存在则创建新的）

        Args:
            session: 会话字典

        Returns:
            保存的文件路径
        """
        if "session_id" not in session or not session["session_id"]:
            new_session = self.create_session()
            session["session_id"] = new_session["session_id"]
            session["created_at"] = new_session["created_at"]

        return self.save_session(session)

    def generate_current_session_id(self):
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"