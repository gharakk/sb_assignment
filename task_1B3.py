
import re

# 1B3A
def hit_counter(log_file_path):
    pattern = re.compile(
        r'([(\d\.)]+) - (jan|-) \[(.*?)\] "(.*?)" (\d+) (\d+) "(.*?)" "(.*?)".*'
    )
    address_dir = {}
    with open(log_file_path, "r") as f:
        for line in f.readlines()[:10]:
            print(line)
            match = re.search(pattern, line)
            line_groups = match.groups()
            print(line_groups)
            print()
            address = line_groups[6]
            if address in address_dir:
                address_dir[address] += 1
            else:
                address_dir[address] = 1

    return address_dir


print(hit_counter("../access.log"))

# 1B3B
# Since this implementation doesn't take advantage of he fact, that the log is not sorted, I wouldn't
# change the implementation.


# 1B3C
# Something like this would give me result for single address
"""
cat access.log | cut -d ] -f2 | cut -d \" -f2 | cut -d ' ' -f2 | grep /mypath | wc -l
"""
