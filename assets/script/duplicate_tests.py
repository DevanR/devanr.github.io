import coverage

def get_hash(s):
    import hashlib
    return str(int(hashlib.sha256(s.encode('utf-8')).hexdigest(), 16) % 10 ** 8)


def set_integer(hash, line_number):
    s_integer = hash
    s_integer += str(line_number)
    return s_integer


def get_max_subset_key(subsets, covered):
    set_covered = set(covered)
    max_key = max(subsets, key=lambda x: len(set(subsets[x])-set_covered))
    return max_key

# http://www.martinbroadhurst.com/greedy-set-cover-in-python.html
def set_cover(universe, subsets):
    """Find a family of subsets that covers the universal set"""
    elements = set(e for s in subsets.values() for e in s)
    # Check the subsets cover the universe
    if elements != universe:
        return None
    covered = set()
    cover = []
    key_cover = []
    # Greedily add the subsets with the most uncovered points
    while covered != elements:
        max_key = get_max_subset_key(subsets, covered)
        key_cover.append(max_key)
        max_subset = subsets[max_key]
        cover.append(max_subset)
        covered |= max_subset

    return sorted(key_cover)


if __name__ == '__main__':

    data = coverage.CoverageData('reverse_coverage.sqlite')
    data.read()

    files = data.measured_files()
    tests = data.measured_contexts()

    # Disregard unnecessary values
    filtered_tests = set()
    for test in tests:
        if any(map(test.__contains__, ["signiq8", "vp", " "])):
            pass
        else:
            filtered_tests.add(test)

    print(f"Total tests = {len(filtered_tests)}")

    # Disregard unnecessary values
    filtered_files = set()
    for file in files:
        if any(map(file.__contains__, ["signiq8", "vp", " "])):
            pass
        else:
            filtered_files.add(file)

    print(f"Total files = {len(filtered_files)}")

    # Create a dictionary of context: [set]
    # where set integers are "hash(file_name)+line_num"
    universe = []
    subsets = {}
    for file in filtered_files:
        file_hash = get_hash(file)
        lines = data.contexts_by_lineno(file)
        for line_num in lines.keys():
            # Include lines that have contexts only
            if lines[line_num] != [' ']:
                # Exclude key of ''
                for line in lines[line_num]:
                    if line != '':
                        if line not in subsets.keys():
                            subsets[line] = set()
                        subsets[line].add(set_integer(file_hash, line_num))
                        universe.append(set_integer(file_hash, line_num))

    print(f"Size of universe = {len(universe)}")
    print(f"Number of subsets = {len(subsets)}")

    key_cover = set_cover(set(universe), subsets)

    print(f"Number of min test = {len(key_cover)}")

    for key in key_cover:
       print(f"{key}")

