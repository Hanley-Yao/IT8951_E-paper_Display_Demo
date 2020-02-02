
# 检查python版本
from sys import version_info
if version_info[0] != 3:
    raise RuntimeError("使用此版本运行代码 Python 3.")
