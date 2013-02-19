import pbldr

print(dir(pbldr))

def test_parse_args():
    '''Test argument parsing'''
    # tbuild = ['pbldr', '-p', 'test', '-p', 'test2']
    tbuild = ['pbldr']
    assert(pbldr.parse_args(tbuild))
