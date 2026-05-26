# core/utils.py
remove_keyword_list = ["|", "data", "RECV <<<<<<<<<<<<<<<<<<<<<<<<<<<"]

def remove_keyword(lst, keyword):
	"""Remove elements from list that match any keyword (exact or substring match)"""
	return [item for item in lst if not any(item == kw or kw in item for kw in keyword)]

def get_data_from_lst(lst, index):
	"""Get element from list by index, return None if out of bounds"""
	index = int(index)
	if index < 0 or index >= len(lst):
		return None
	return lst[index]
	
def get_multi_data_from_lst(lst, index, length):
	"""Get multiple consecutive elements from list, joined as string"""
	result = []
	for i in range(length):
		element = get_data_from_lst(lst, int(index) + i)
		if element is None:
			break
		result.append(element)
	return ''.join(result)
