

if __name__ == '__main__':

    def append_obj(
            arr,
            val
    ):
        arr.append(val)
        return

    a = ['one', 'two']
    append_obj(arr=a, val='three')
    print(a)

    try:
        print('start...')
        print(abc)
    except Exception as ex:
        raise ex
    finally:
        print('Final cleanup done..')