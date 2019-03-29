fname_in = 'server.py'
fname_out = 'server_async.py'


text = ''
remove = False
for line in open(fname_in, 'r'):
    if '# ' in line:
        line = line.replace('# ', '')
        remove = True
    elif remove:
        remove = False
        continue
    text += line


open(fname_out, 'w').write(text)

