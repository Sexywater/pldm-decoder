# PLDM Decoder 项目优化计划

> 这是一个 PLDM trace 处理脚本，用于解析 raw data。优化原则：保持简洁，不做过度工程。

---

## 优化项 1: 消除 `protocol/reader.py` 中重复的 ini 值解析

### 问题
`get_multi_data_from_block()` 每次调用都执行 `ini_value.split(';')` 解析 `"index;length"` 字符串，而同一个 key 在单次处理中可能被多次调用。例如在 `get_pdr.py` 中，`"GET_PDR_RESPONSE"` section 被多次查询。

### 方案
在 `protocol/reader.py` 中添加一个简单的缓存层，将 `"index;length"` 的解析结果缓存起来（使用 `functools.lru_cache` 或手动 dict），避免重复的字符串分割和类型转换。

### 涉及文件
- `protocol/reader.py`

---

## 优化项 2: 拆分 `handlers/get_pdr.py` 中的巨型函数

### 问题
`process_get_pdr_payload()` 约 120 行，处理 4 种 PDR 类型（terminus locator / numeric sensor / state sensor），所有逻辑挤在一个函数里，可读性差。

### 方案
将每种 PDR 类型的解析逻辑提取为独立函数：
- `_parse_terminus_locator_pdr(block, vdm_payload)`
- `_parse_numeric_sensor_pdr(block, vdm_payload)`
- `_parse_state_sensor_pdr(block, vdm_payload)`

主函数只做请求/响应判断和 PDR 类型分发。

### 涉及文件
- `handlers/get_pdr.py`

---

## 优化项 3: 统一 handler 中的请求/响应判断

### 问题
各 handler 中判断请求/响应使用了不同的 magic number，散落在各处，难以维护：

| 文件 | 判断条件 |
|------|---------|
| `platform_event_msg.py` | `len(block) == 25 and block[-4:] == ["00","00","00","00"]` |
| `get_sensor_reading.py` | `len(block) == 25 and block[-2:] == ["00","00"]` |
| `get_state_sensor_readings.py` | `len(block) == 25 and block[-2:] == ["00","00"]` |
| `get_terminus_uid.py` | `len(block) == 21` |
| `set_tid.py` | `len(block) == 25 and block[-4:] == ["00","00","00","00"]` |
| `get_tid.py` | `len(block) == 21` |
| `get_pldm_version.py` | `len(block) == 29 and block[-2:] == ["00","00"]` |
| `get_pldm_commands.py` | `len(block) == 29 and block[-3:] == ["00","00","00"]` |
| `get_pdr.py` | `len(block) == 37 and block[-3:] == ["00","00","00"]` |

### 方案
在 `protocol/reader.py` 中添加一个简单的工具函数：
```python
def is_request_block(block, expected_len, trailer_len=0):
    """判断 block 是否为请求消息"""
    if len(block) != expected_len:
        return False
    if trailer_len > 0:
        return block[-trailer_len:] == ["00"] * trailer_len
    return True
```

### 涉及文件
- `protocol/reader.py`
- 所有 `handlers/*.py`

---

## 优化项 4: 修复 `core/types.py` 中的拼写错误

### 问题
- `parse_range_filed_support` -> 应为 `parse_range_field_support`（filed -> field）
- `to_decimal()` 的 if/else 可简化为三元表达式

### 方案
- 修正函数名，保留旧名称作为别名（或统一更新所有调用点）
- 简化 `to_decimal()` 为一行

### 涉及文件
- `core/types.py`
- `handlers/get_pdr.py`（调用方）

---

## 优化项 5: 消除 `auto_translator.py` 中的重复翻译逻辑

### 问题
`_on_selection_changed()` 和 `_monitor_loop()` 中有大量重复的翻译逻辑（文本获取、过滤、翻译、显示），代码几乎完全一样。

### 方案
提取公共逻辑为 `_do_translate(text)` 方法，两个函数都调用它。

### 涉及文件
- `auto_translator.py`

---

## 优化项 6: 简化 `parser/log_processor.py` 的职责

### 问题
`process_file()` 同时做了三件事：过滤行、打印到终端、提取 block。混合了 I/O 和数据处理。

### 方案
将打印逻辑从 `process_file()` 中分离，让函数只负责过滤和提取，打印由调用方决定。

### 涉及文件
- `parser/log_processor.py`
- `pldm_decoder.py`（调用方）

---

## 执行顺序

1. **优化 4** (修复拼写) - 无风险，快速完成
2. **优化 1** (reader 缓存) - 基础设施优化
3. **优化 3** (统一请求判断) - 减少 magic number
4. **优化 2** (拆分 get_pdr.py) - 较大重构
5. **优化 6** (log_processor 简化) - 影响主流程
6. **优化 5** (auto_translator 去重) - 独立工具

---

## 不做的优化（保持现状）

以下优化项经评估后决定不做，以保持代码简洁：

| 优化项 | 原因 |
|--------|------|
| 动态调度 DISPATCH 表 | 当前硬编码表清晰直观，只有 9 个条目，动态加载反而增加复杂度 |
| 类型注解 | 脚本工具不需要，增加维护负担 |
| 异常处理/日志 | raw data 处理工具，print 足够，过度错误处理会掩盖问题 |
| 补充单元测试 | 现有测试已覆盖核心路径 |
| 缩进风格 | 保持原有 tab 缩进不变 |
