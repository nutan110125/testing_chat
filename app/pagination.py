from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def paginatorData(data,limit,page):
    paginator = Paginator(data,limit)
    try:
        list2 = paginator.page(page)
    except PageNotAnInteger:
        list2 = paginator.page(1)
        page = 1
    except EmptyPage:
        list2 = paginator.page(paginator.num_pages)
        page = paginator.num_pages
    
    return list2,page,paginator