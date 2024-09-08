def slotnum_to_bname(slot:str):
    if slot in ['1', '2', '3', '4', '5', '6', '7', '8', '8a', '9', '10', '11', '12']:
        return f'B{slot}'.upper()
    else:
        return slot.lower()

def bname_to_slotnum(bname:str):
    if bname in ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9', 'B10', 'B11', 'B12']:
        return bname[1:].lower()
    else:
        return bname.lower()