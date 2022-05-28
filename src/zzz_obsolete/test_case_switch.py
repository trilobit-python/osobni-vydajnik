# Because Python has first-class functions they can
# be used to emulate switch/case statements

import timeit
import time


class MyTimer:

    def __init__(self):
        self.start = time.time()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end = time.time()
        runtime = end - self.start
        msg = 'The function took {time} seconds to complete'
        print(msg.format(time=runtime))


def dispatch_if(operator, x, y):
    if operator == 'add':
        return x + y
    elif operator == 'sub':
        return x - y
    elif operator == 'mul':
        return x * y
    elif operator == 'div':
        return x / y
    else:
        return None


def dispatch_dict(operator, x, y):
    return {
        'add': lambda: x + y,
        'sub': lambda: x - y,
        'mul': lambda: x * y,
        'div': lambda: x / y,
    }.get(operator, lambda: None)()


def test_time(code_stmt):
    times = timeit.repeat(stmt='x = dispatch_if(\'mul\', 2, 8)', repeat=1,
                          number=1000000, globals=globals())
    print(f'{code_stmt} time: {times}')


if __name__ == '__main__':
    # test_time( 'dispatch_dict (\'add\', 8, 2)' )
    # test_time( 'dispatch_dict (\'div\', 8, 2)' )
    # test_time( 'dispatch_if (\'add\', 8, 2)' )
    # test_time( 'dispatch_if (\'div\', 8, 2)' )

    print('Test dispatch_if')
    with MyTimer():
        for i in range(0, 1000000):
            dispatch_if('div', i, 2)

    print('Test dispatch_if add')
    with MyTimer():
        for i in range(0, 1000000):
            dispatch_if('add', i, 2)

    print('Test dispatch_dict')
    with MyTimer():
        for i in range(0, 1000000):
            dispatch_dict('div', i, 2)

    print('Test dispatch_dict add')
    with MyTimer():
        for i in range(0, 1000000):
            dispatch_dict('add', i, 2)
