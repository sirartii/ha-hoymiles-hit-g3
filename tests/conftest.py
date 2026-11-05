"""Shared Home Assistant fixtures and a synthetic HIT-G3 register image."""

import pytest

from custom_components.hoymiles_hit_g3.config_flow import connection_schema


@pytest.fixture
def settings():
    return connection_schema({})({"host": "192.0.2.10"})


@pytest.fixture
def raw():
    values = {address: 0 for address in range(100)}
    values.update({0: 3, 1: 10216, 3: 2, 4: 10000, 19: 0, 20: 0, 21: 0, 22: 0})
    for address in (26, 45, 73, 77, 87, 91):
        values[address] = 5
    for index in range(4):
        values.update({27 + index * 3: 4000, 28 + index * 3: 100, 29 + index * 3: 400})
    values.update(
        {
            46: 520,
            48: 65535,
            49: 63536,
            50: 65535,
            51: 64496,
            60: 8100,
            65: 0,
            66: 5000,
            74: 500,
            75: 600,
            76: 700,
            78: 65386,
            79: 70,
            80: 65501,
            92: 100,
            93: 200,
            94: 300,
            113: 50,
            114: 55,
            115: 40,
            190: 0,
            191: 1590,
            325: 100,
            326: 565,
            327: 440,
            328: 1250,
            1022: 1,
            1024: 200,
            1025: 50,
            1046: 1,
            1078: 65535,
            1079: 64536,
            1080: 0,
            1081: 500,
            1082: 0,
            1083: 200,
            2169: 2100,
        }
    )
    values.update({address: 0 for address in range(2000, 2058)})
    values.update({address: 0 for address in range(2100, 2136)})
    values.update(
        {
            2001: 60000,
            2029: 10000,
            2031: 8000,
            2041: 20000,
            2049: 3000,
            2057: 40000,
            2100: 200,
            2128: 150,
        }
    )
    return values
