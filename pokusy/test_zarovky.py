# Transcribed Image Text from this Question
#
# There are N bulbs, numbered from 1 to N, arranged in a row. The first bulb is
# plugged into the power socket and each successive bulb is connected to the
# previous one (the second bulb to the first, the third bulb to the second,
# etc.). Initially, all the bulbs are turned off. At moment K(for K from 0 to
# N-1), we turn on the AK-th bulb. A bulb shines if it is on and all the
# previous bulbs are turned on too. Write a function solution that, given an
# array A of N different integers from 1 to N returns the number of moments for
# which every turned on bulb shines.
#
# Examples:
#   1. Given A=[2, 1, 3, 5, 4], the
# function should return 3. • At the oth moment only the 2nd bulb is turned on,
# but it does not shine because the previous one is not on. • At the 1st moment
# two bulbs are turned on (1st and 2nd), and both of them shine. • At the 2nd
# moment three bulbs are turned on (1st, 2nd and 3rd) and all of them chine • At
# the oth moment only the 2nd bulb is turned on, but it does not shine because
# the previous one is not on. • At the 1st moment two bulbs are turned on (1st
# and 2nd) and both of them shine. • At the 2nd moment three bulbs are turned on
# (1st, 2nd and 3rd) and all of them shine. • At the 3rd moment four bulbs are
# turned on (1st, 2nd, 3rd and 5th), but the 5th bulb does not shine because the
# previous one is not turned on. • At the 4th moment five bulbs are turned on
# (1st, 2nd, 3rd, 4th and 5th) and all five of them shine. There are three
# moments (1st, 2nd and 4th) when every turned on bulb shines.
#   2. Given A=[2, 3, 4, 1,5), the function should return 2 (at the 3rd and 4th moment every turned
# on bulb shines).
#   3. Given A=(1,3, 4, 2, 5), the function should return 3 (at
# the Oth, 3rd and 4th moment every turned on bulb shines). Write an efficient
# algorithm for the following assumptions: • N is an integer within the range
# [1..100,000); the elements of A are all distinct; each element of array A is
# an integer within the range 1..N.
#


def reseni(A):
    n_last_on = 0
    set_of_not_on = set()
    max_in_set_of_not_on = 0
    n_return = 0

    for i in A:
        # print('Before ', i, n_last_on, str(set_of_not_on))
        if len(set_of_not_on) == 0 and i == (n_last_on + 1):
            # all before were shinning
            # print('A')
            n_return += 1
            n_last_on = i
            max_in_set_of_not_on = 0
        else:
            if len(set_of_not_on) > 0:
                # use previous switch-off bulbs
                # print('B')
                bOK = True
                for ii in range(n_last_on + 1, max(i, max_in_set_of_not_on) + 1):
                    # print('ii', ii, end=', ')
                    if ii == i or ii in set_of_not_on:
                        pass  # OK
                    else:
                        bOK = False  # missing bulb

                if bOK:
                    # print('C')
                    set_of_not_on = set()
                    n_return += 1
                    n_last_on = max(i, max_in_set_of_not_on)
                else:
                    # print('D')
                    set_of_not_on.add(i)
                    if i > max_in_set_of_not_on:
                        max_in_set_of_not_on = i
            else:
                # add to switch off bulbs
                # print('C')
                set_of_not_on.add(i)
                if i > max_in_set_of_not_on:
                    max_in_set_of_not_on = i

        # print('After ', i, n_last_on, str(set_of_not_on))
    return n_return


def test_one(str_input, expected_value):
    A = eval(str_input)
    res = reseni(A)
    msg = f'data:{A} expected:{expected_value} got:{res}  '
    if res == expected_value:
        msg = 'OK    ' + msg
    else:
        msg += 'ERROR ' + msg
    print(msg)


test_one('[2, 1, 3, 5, 4]', 3)
test_one('[2, 3, 4, 1, 5]', 2)
test_one('[1, 3, 4, 2, 5]', 3)
