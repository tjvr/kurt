tests_run = 0
tests_failed = 0
test_results = {}


print 'Testing!'


def test_cons(cons, encoded, value):
    global tests_run, tests_failed
    failed = False
    
    def fail(failed=failed):
        if not failed:
            print 'Test #%i, %s:' % (tests_run, value)
        failed = True
    
    parsed = None
    try:
        parsed = cons.parse(encoded)
    except Exception, e:
        if not failed: fail()
        failed = True
        print '  Error: %s' % e
    else:
        if not parsed == value or parsed != value: # Stupid but might forget to do __ne__ as well as __eq__...
            if not failed: fail()
            failed = True
            print '  %s.parse(%s) gave <%s> not <%s>' % (cons, repr(encoded), repr(parsed), repr(value))
    
    built = None
    try:
        built = cons.build(value)
    except Exception, e:
        if not failed: fail()
        failed = True
        print '  Error: %s' % e
    else:
        if not built == encoded or built != encoded:
            if not failed: fail()
            failed = True
            print '  %s.build(%s) gave <%s> not <%s>' % (cons, repr(value), repr(built), repr(encoded))
    
    if failed:
        tests_failed += 1
        test_results[tests_run] = (cons, encoded, value, parsed, built)
    tests_run += 1


def tests_finish():
    if tests_run:
        if tests_failed:
            print 'Failed %i of %i tests.' % (tests_failed, tests_run)
            print '(See results in test_results.)'
        else:
            print 'Ran all %i tests successfully!' % tests_run
    else:
        print 'No tests run!'
    print '###'
    print


def retry_test(index):
    test_cons(*test_results[index][:3])
    (cons, encoded, value) = test_results[index][:3]


