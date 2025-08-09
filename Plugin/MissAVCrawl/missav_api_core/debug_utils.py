#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试工具模块
提供统一的调试输出功能，避免干扰JSON输出
"""

import sys

def debug_print(*args, **kwargs):
    """调试输出到stderr，避免干扰JSON输出"""
    print(*args, file=sys.stderr, **kwargs)