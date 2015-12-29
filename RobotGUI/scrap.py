test = {"lol": 3, "kek": 4, "haha": '5.012309128309182039'}

z = [x for x in test.itervalues()]

print any((type(x) == str) for x in test.itervalues())

print z
for x in test.itervalues():
    print x

if 0 in test.values():
    print "kek"