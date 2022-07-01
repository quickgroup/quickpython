import logging, math
from urllib.parse import urlencode
from .func import *
log = logging.getLogger(__name__)


class Pagination:

    def __init__(self, rows, page, page_size, total, params):
        self.rows = [] if empty(rows) else rows
        self.page = page
        self.page_size = page_size
        self.page_total = self.__math_ceil__(total, page_size)
        self.total = total
        self.style = 'simple'       # 页码样式
        self.params = {} if empty(params) else params   # 请求参数

    def items(self):
        return self.rows

    def render(self):
        """渲染页码按钮"""
        def href_li(page, page_font=None):
            page_font = page_font if page_font else page
            return '<li><a href="?{}">{}</a></li>'.format(urlencode({**self.params, **{'page': page}}), page_font)

        def disable_li(page):
            return '<li class="disabled"><span>{}</span></li>'.format(page)

        page_num_links = ""
        prev_page = self.page - 1
        prev_btn = disable_li(1) if prev_page <= 0 else href_li(prev_page, '上一页')
        if self.page < self.page_total:
            next_page = self.page if self.page + 1 > self.page_total else self.page + 1
            log.debug("next_page={}".format(next_page))
            next_btn = href_li(next_page, '下一页')
        else:
            next_btn = ''
        if self.style != 'simple':
            page_num_links = ""     # 输出页码按钮
        return """<ul class="pager">{}{}{}</ul>""".format(prev_btn, page_num_links, next_btn)

    @staticmethod
    def __math_ceil__(total, page_size):
        return math.ceil(total / page_size)

    def __dict__(self):
        return {
            'rows': [dict(it) for it in self.rows],
            'page': self.page, 'page_size': self.page_size,
            'total': self.total, 'page_total': self.page_total,
        }
