import functools
import itertools


class Rom:
    def __init__(self, memory):
        self.memory = memory
        self.ranges = []
        self.content = {}
        self.labels = {}
        self.comments = {}

    def get_type(self, address):
        r = self.__find_range(address)

        if not r:
            return "unknown"

        return r[1]

    def mark_data(self, begin, end):
        self.__mark_range(begin, end, 'data')

    def mark_code(self, begin, end):
        self.__mark_range(begin, end, 'code')

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

    def get_label_at(self, address):
        return self.labels.get(address, None)

    def get_labels(self):
        for address in sorted(self.labels.keys()):
            yield address, self.labels[address]

    def name_label(self, address, new_name):
        label = self.labels.get(address, ("", []))
        name, callers = label
        self.labels[address] = new_name, callers

    def add_comment(self, address, tag, comment):
        comments = self.comments.get(address, list())
        comments.append((tag, comment))
        self.comments[address] = comments

    def get_comments_at(self, address):
        return self.comments.get(address, set())

    def __mark_range(self, begin, end, range_type):
        """ begin is inclusive, end is exclusive, to be coherent with range()"""
        existing_range = self.__find_overlapping_range(begin, end)
        new_range = ((begin, end), range_type)

        if not existing_range:
            self.ranges.append(new_range)
        else:
            self.ranges.remove(existing_range)
            ((b_old, e_old), t_old) = existing_range
            ((b_new, e_new), t_new) = new_range

            if b_old < b_new:
                # Existing rang is flowing on the left
                new_old_left = (b_old, b_new), t_old
                self.ranges.append(new_old_left)

            if e_old > e_new:
                # Existing rang is flowing on the right
                new_old_right = (e_new, e_old), t_old
                self.ranges.append(new_old_right)

            self.ranges.append(new_range)

        self.__merge_adjacent_ranges()

    def __find_overlapping_range(self, begin, end):
        for r in sorted(self.ranges):
            limits = r[0]
            if (begin < limits[0] < end) or (limits[0] <= begin < limits[1]):
                return r

        return None

    def __find_range(self, address):
        found_range = [r for r in self.ranges if address in range(*(r[0]))]
        return found_range[0] if found_range else None

    def __merge_adjacent_ranges(self):
        new_ranges = functools.reduce(merge_neighbours, sorted(self.ranges), [])
        self.ranges = new_ranges


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
