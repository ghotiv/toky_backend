import arrow

from my_conf import TZ

def func_left_join(l_left, l_right, index_names):
    left_sorted_list = sorted([(tuple([i[j] for j in index_names]), i) for i in l_left],
                              key=lambda x: x[0])
    right_dict = dict([(tuple([i[j] for j in index_names]), i)
                       for i in l_right])
    return [dict(l[1], **right_dict.get(l[0], {})) for l in left_sorted_list]


def to_tztime(time_int,format_time=True):
    if not time_int:
        return ''
    res = arrow.get(int(time_int)).to(TZ)
    if format_time:
        res = res.format('YYYY-MM-DD HH:mm:ss')
    return res

