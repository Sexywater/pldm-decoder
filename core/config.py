# core/config.py
import configparser
from functools import lru_cache

# ini filename constants
INI_TYPE0 = "pldm_type0.ini"
INI_TYPE2 = "pldm_type2.ini"
INI_VMD_HEADER = "pldm_vmd_header.ini"
INI_NIC_SENSOR = "nic_sensor.ini"


@lru_cache(maxsize=8)
def _read_config(file_path):
    """Cache loaded ini config to avoid re-reading files on every query"""
    config = configparser.ConfigParser()
    config.read(file_path, encoding='utf-8')
    return config


def get_value_from_ini(file_path, section, key):
    config = _read_config(file_path)
    if not config.has_option(section, key):
        return None
    return config.get(section, key)
