"""
Subprocess utilities / 子进程工具
"""
import subprocess
import os

# 隐藏 Windows CMD 窗口 / Hide Windows CMD window
if os.name == 'nt':
    SUBPROCESS_CREATE_FLAGS = subprocess.CREATE_NO_WINDOW
else:
    SUBPROCESS_CREATE_FLAGS = 0


def run_hidden(*args, **kwargs):
    """Run subprocess with hidden window / 运行隐藏窗口的子进程"""
    if os.name == 'nt':
        if 'creationflags' not in kwargs:
            kwargs['creationflags'] = SUBPROCESS_CREATE_FLAGS
        else:
            # Combine existing flags with the no window flag
            kwargs['creationflags'] |= SUBPROCESS_CREATE_FLAGS
    return subprocess.run(*args, **kwargs)
