# TODO
# input: total, per_page, page
# output:
# a range of item numbers to display for each page (showing 1-10, 10-20, ..etc)
# has next method (whether the next page exists)
# has previous method (whether the previous page exists)

import math
from math import ceil

class Pagination():

    def __init__(self, total, per_page, page):
        self.total = total
        self.per_page = per_page
        self.num_pages = int(ceil(self.total/self.per_page))
        self.page = page
        self.from_item = (self.page -1)*self.per_page + 1
        self.to_item = min(self.page*self.per_page, self.total)
        self.pagediv = int(ceil(self.page/5))
        self.from_page = (self.pagediv -1)*5 + 1
        self.to_page = min(self.pagediv*5, self.num_pages)



    # # has next
    def has_next(self):
        return self.page < self.num_pages

    # # has_previous
    def has_previous(self):
        return self.page > 1

# How to use:
# p= Pagination(0, 6, 1)
# print("num_pages = {0}".format(p.num_pages))
# print("\n")
# print("from_item = {0}".format(p.from_item))
# print("to_item = {0}".format(p.to_item))
# print("\n")
# print(p.has_next())
# print(p.has_previous())
# print("\n")
# print("from_page = {0}".format(p.from_page))
# print("to_page = {0}".format(p.to_page))
# print("pagediv = {0}".format(p.pagediv))

