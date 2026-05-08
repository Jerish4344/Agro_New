from django import template
from django.utils.html import format_html, mark_safe
from django.contrib.admin.views.main import PAGE_VAR

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def in_list(value, the_list):
    """Check if value is in the list"""
    if the_list is None:
        return False
    return value in the_list


@register.simple_tag
def fixed_paginator_number(change_list, i):
    """
    Generate an individual page index link in a paginated list.
    Fixed for Django 6.0 compatibility with format_html.
    """
    html_parts = []
    start = i == 1
    end = i == change_list.paginator.num_pages
    spacer = i in (".", "…")
    current_page = i == change_list.page_num

    if start:
        if change_list.page_num > 1:
            link = change_list.get_query_string({PAGE_VAR: change_list.page_num - 1})
            html_parts.append(format_html(
                '<li class="page-item previous">'
                '<a class="page-link" href="{}" data-dt-idx="0" tabindex="0">«</a>'
                '</li>',
                link
            ))
        else:
            html_parts.append(mark_safe(
                '<li class="page-item previous disabled">'
                '<a class="page-link" href="#" data-dt-idx="0" tabindex="0">«</a>'
                '</li>'
            ))

    if current_page:
        html_parts.append(format_html(
            '<li class="page-item active">'
            '<a class="page-link" href="javascript:void(0);" data-dt-idx="3" tabindex="0">{}</a>'
            '</li>',
            i
        ))
    elif spacer:
        html_parts.append(mark_safe(
            '<li class="page-item">'
            '<a class="page-link" href="javascript:void(0);" data-dt-idx="3" tabindex="0">…</a>'
            '</li>'
        ))
    else:
        query_string = change_list.get_query_string({PAGE_VAR: i})
        end_class = "end" if end else ""
        html_parts.append(format_html(
            '<li class="page-item">'
            '<a href="{}" class="page-link {}" data-dt-idx="3" tabindex="0">{}</a>'
            '</li>',
            query_string, end_class, i
        ))

    if end:
        if change_list.page_num < i:
            link = change_list.get_query_string({PAGE_VAR: change_list.page_num + 1})
            html_parts.append(format_html(
                '<li class="page-item next">'
                '<a class="page-link" href="{}" data-dt-idx="7" tabindex="0">»</a>'
                '</li>',
                link
            ))
        else:
            html_parts.append(mark_safe(
                '<li class="page-item next disabled">'
                '<a class="page-link" href="#" data-dt-idx="7" tabindex="0">»</a>'
                '</li>'
            ))

    return mark_safe(''.join(str(part) for part in html_parts))
