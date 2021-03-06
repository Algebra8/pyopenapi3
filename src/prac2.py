from src.pyopenapi3.objects import ServerObject


z1 = {
    'url': '/'
}

s1 = ServerObject(**z1)

z2 = {
    'url': '/',
    'description': 'some server',
    'variables': {'enum'}
}

