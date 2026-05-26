# core/types.py
# Type conversion utilities extracted from pldm_common.py

# Convert hex data to a specified type
def hex_to_type(hex_str, typ):
	bits = int(typ[4:])
	num = int(hex_str, 16)
	mask = (1 << bits) - 1
	num &= mask
	if typ.startswith('sint') and num & (1 << (bits - 1)):
		num -= (1 << bits)
	return num
	
def to_decimal(value):
	return {"hex": value, "dec": int(str(value), 16)} if value else None

def parse_support_thresholds(bin_value):
	bin_value = bin_value.zfill(8)
	
	threshold_mapping = {
		5: "lowerThresholdFatal",
		4: "lowerThresholdCritical",
		3: "lowerThresholdWarning",
		2: "upperThresholdFatal",
		1: "upperThresholdCritical",
		0: "upperThresholdWarning"
	}
	
	supported_thresholds = []
	for bit_pos, threshold_name in threshold_mapping.items():
		bit_val = bin_value[7 - bit_pos]
		if bit_val == "1":
			supported_thresholds.append(threshold_name)
	return supported_thresholds if supported_thresholds else "no supported threshold"
	
def parse_range_field_support(bin_value):
	"""Parse range field support bits into human-readable list"""
	bin_value = bin_value.zfill(8)
	
	field_mapping = {
		6: "fatalLow field supported",
		5: "fatalHigh field supported",
		4: "criticalLow field supported",
		3: "criticalHigh field supported",
		2: "normalMin field supported",
		1: "normalMax field supported",
		0: "nominalValue field supported"
	}
	
	supported_fields = []
	for bit_pos, field_name in field_mapping.items():
		bit_val = bin_value[7 - bit_pos]
		if bit_val == "1":
			supported_fields.append(field_name)
	
	return supported_fields if supported_fields else "no supported field"

# Alias for backward compatibility
parse_range_filed_support = parse_range_field_support
