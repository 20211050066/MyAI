import os
import config_data as config
import hashlib


def check_md5(md5_str: str) -> bool:
    """
    检查传入的md5字符串是否已经处理
    """
    if not os.path.exists(config.md5_path):
        open(config.md5_path, 'w', encoding='utf-8').close()
        return False
    else:
        for line in open(config.md5_path, 'r', encoding='utf-8').readlines():
            line = line.strip()
            if line == md5_str:
                return True
        return False


def save_md5(md5_str: str) -> None:
    """
    将传入的md5字符串记录到文件保存
    """
    with open(config.md5_path, 'a', encoding='utf-8') as f:
        f.write(md5_str + '\n')


def get_string_md5(input_str: str, encoding='utf-8') -> str:
    """
    获取字符串的md5值
    """
    str_bytes = input_str.encode(encoding=encoding)
    md5_obj = hashlib.md5()
    md5_obj.update(str_bytes)
    md5_hex = md5_obj.hexdigest()
    return md5_hex


class KnowledgeBaseService(object):
    def __init__(self):
        self.chroma = None
        self.spliter = None

    def upload_by_str(self, data, filename):
        """
        将传入的字符串进行向量化，存入到向量数据库中
        """
        pass
