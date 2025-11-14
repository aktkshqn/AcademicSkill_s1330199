# src/voicing.py
from .config import F0_THRESHOLD

def is_voiced_by_flag(flag):
    """librosa の voiced_flag (bool array element) を元に判定"""
    return bool(flag)

def is_voiced_by_f0(f0_value):
    """fallback: F0閾値で判定"""
    return f0_value > F0_THRESHOLD

def is_voiced(f0_value, flag=None):
    """有声音判定"""
    if flag is not None:
        return is_voiced_by_flag(flag)
    else:
        return is_voiced_by_f0(f0_value)