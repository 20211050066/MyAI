def check_md5():
    """
    检查传入的md5字符串是否已经处理
    """
    pass

def save_md5():
    """
    将传入的md5字符串记录到文件保存
    """
    pass
def get_string_md5(string: str) -> str:
    """
    获取字符串的md5值
    """
    pass

class KnowledgeBaseService(object):
    def __init__(self):
        self.chroma = None
        self.spliter = None

    def upload_by_str(self,data,filename):
        """
        将传入的字符串进行向量化，存入到向量数据库中
        """
        pass