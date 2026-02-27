import functools
import itertools
from collections import defaultdict


class Rom:
    def __init__(self, memory):
        self.memory = memory
        self.regions = []
        self.content = {}
        self.labels = {}
        self.comments = defaultdict(list)
        self.descriptions = defaultdict(list)
        self.tags = defaultdict(list)
        self.nostring_regions = []

    def get_type(self, address):
        r = self.__find_region(address)

        if not r:
            return "unknown"

        return r[1]

    def mark_data(self, begin, end):
        self.__mark_region(begin, end, 'data')

    def mark_code(self, begin, end):
        self.__mark_region(begin, end, 'code')

    def add_content(self, address, content):
        self.content[address] = content

    def get_content(self, begin, end):
        addresses = sorted(self.content.keys())
        addresses = itertools.dropwhile(lambda k: k < begin, addresses)
        addresses = itertools.takewhile(lambda k: k < end, addresses)

        for address in addresses:
            yield address, self.get_type(address), self.content[address]

    def get_content_at(self, address):
        return address, self.get_type(address), self.content.get(address, None)

    def add_labels(self, labels):
        for key, value in labels.items():
            if key in self.labels:
                name, callers = self.labels[key]
                callers = list(sorted(set(callers + value[1])))
                self.labels[key] = name, callers
            else:
                self.labels[key] = value
                self.__split_content_at(key)

    def get_label_at(self, address):
        return self.labels.get(address, None)

    def get_labels(self):
        for address in sorted(self.labels.keys()):
            yield address, self.labels[address]

    def name_label(self, address, new_name):
        label = self.labels.get(address, ("", []))
        name, callers = label
        self.labels[address] = new_name, callers

        self.__split_content_at(address)

    def add_comment(self, address, tag, comment, end_address):
        self.comments[address].append((tag, comment, end_address))

    def get_comments_at(self, address):
        return self.comments.get(address, list())

    def add_description(self, address, comment):
        self.descriptions[address].append(comment)

    def get_description_at(self, address):
        return self.descriptions.get(address, set())

    def add_tag(self, address, tag):
        self.tags[address].append(tag)

    def get_tags_at(self, address):
        return self.tags.get(address, set())

    def add_nostring_region(self, start, end):
        self.nostring_regions.append((start, end))

    def is_in_nostring_region(self, address):
        return any(start <= address <= end for start, end in self.nostring_regions)

    def __split_content_at(self, address):
        if address >= len(self.memory):
            return

        if self.get_type(address) != 'data':
            return

        if address in self.content.keys():
            return

        content_address = itertools.takewhile(lambda a: a <= address, sorted(self.content.keys()))
        content_address = list(content_address)

        if not content_address:
            return

        content_address = content_address[-1]
        adjusted_length = address - content_address

        content = self.get_content_at(content_address)

        address, region_type, data = content

        if len(data) < adjusted_length:
            return

        del self.content[content_address]

        self.add_content(address, data[:adjusted_length])
        self.add_content(address + adjusted_length, data[adjusted_length:])

    def __mark_region(self, begin, end, region_type):
        """ begin is inclusive, end is exclusive, to be coherent with range()"""
        existing_region = self.__find_overlapping_region(begin, end)
        new_region = ((begin, end), region_type)

        if not existing_region:
            self.regions.append(new_region)
        else:
            self.regions.remove(existing_region)
            ((b_old, e_old), t_old) = existing_region
            ((b_new, e_new), t_new) = new_region

            if b_old < b_new:
                # Existing region is flowing on the left
                new_old_left = (b_old, b_new), t_old
                self.regions.append(new_old_left)

            if e_old > e_new:
                # Existing region is flowing on the right
                new_old_right = (e_new, e_old), t_old
                self.regions.append(new_old_right)

            self.regions.append(new_region)

        self.__merge_adjacent_regions()

    def __find_overlapping_region(self, begin, end):
        for r in sorted(self.regions):
            limits = r[0]
            if (begin < limits[0] < end) or (limits[0] <= begin < limits[1]):
                return r

        return None

    def __find_region(self, address):
        found_region = [r for r in self.regions if address in range(*(r[0]))]
        return found_region[0] if found_region else None

    def __merge_adjacent_regions(self):
        new_regions = functools.reduce(merge_neighbours, sorted(self.regions), [])
        self.regions = new_regions


def merge_neighbours(acc, new):
    if len(acc) > 0:
        previous = acc[-1]
        ((b_old, e_old), t_old) = previous
        ((b_new, e_new), t_new) = new

        if t_old == t_new and e_old == b_new:
            return acc[:-1] + [((b_old, e_new), t_new)]
        else:
            return acc + [new]

    else:
        return [new]
