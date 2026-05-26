# protocol/payload.py
# Payload factory and output formatting
from parser.vdm_header import format_vdm_header


def new_payload():
	"""Factory function to create a standard vdm_payload dict"""
	return {"output": [], "verbose": []}


def decode_payload(block, vdm_payload, verbose=False):
	if not vdm_payload:
		return
	
	output_list = vdm_payload.get("output", [])
	verbose_list = vdm_payload.get("verbose", [])
	if len(output_list) == 0 and len(verbose_list) == 0:
		return
	
	header = format_vdm_header(block)
	if header:
		print(header)

	if verbose and verbose_list:
		if output_list:
			print("BASIC:		" + " ".join(map(str, output_list)))
		if verbose_list:
			print("VERBOSE:\t" + " ".join(map(str, verbose_list)))
	else:
		for item in output_list:
			print("BASIC:	", item)
