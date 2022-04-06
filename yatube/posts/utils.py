from django.conf import settings
from django.core.paginator import Paginator


def get_page_obj(obj_list, page_number):
    paginator = Paginator(obj_list, settings.POSTS_ON_PAGE)
    return paginator.get_page(page_number)
